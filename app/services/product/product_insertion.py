from typing import List, Dict, Any, Tuple
from fastapi import HTTPException
from sqlalchemy import Table, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
import logging
from app.models.product import Product
from app.models.product_image import ProductImage
from datetime import datetime

logger = logging.getLogger(__name__)

class BulkInserter:
    def __init__(self, db, supplier_id: int):
        self.db = db
        self.supplier_id = supplier_id
        self.batch_size = 100
        self.product_ids: set[str] = set()

    async def process_sheets(self, sheets_data: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str], image_map: Dict[str, str]) -> Dict[str, Any]:
        try:
            product_sheets, image_sheets = self._classify_sheets(sheets_data, column_map, image_map)
            product_result = await self._process_products(product_sheets, column_map)
            await self.db.commit()
            await self._refresh_product_ids()

            image_result = await self._process_images(image_sheets, image_map)
            await self.db.commit()

            return {
                "products": product_result,
                "images": image_result
            }
        except Exception as e:
            await self.db.rollback()
            logger.exception("Bulk insert failed")
            raise HTTPException(status_code=500, detail=str(e))

    def _classify_sheets(self, sheets_data: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str], image_map: Dict[str, str]) -> Tuple[List, List]:
        product_cols = set(column_map.values())
        image_cols = set(image_map.values())
        product_sheets, image_sheets = [], []

        for sheet in sheets_data:
            sheet_name, columns, _ = sheet
            if any(c in product_cols for c in columns):
                product_sheets.append(sheet)
            image_sheets.append(sheet)

        return product_sheets, image_sheets

    async def _refresh_product_ids(self):
        result = await self.db.execute(select(Product.product_id))
        self.product_ids = {
            str(r[0]).strip().upper() for r in result if r[0] is not None
        }
  
    def _normalize_value(self, value: Any) -> str:

        if value is None:
            return ""
        try:
            if isinstance(value, (int, float)):
                if float(value).is_integer():
                    return str(int(value)).strip().upper()
            return str(value).strip().upper()
        except (ValueError, TypeError):
            return str(value).strip().upper()

    def _find_product_id_match(self, row: Dict[str, Any]) -> str:

        if not self.product_ids:
            logger.warning("No product IDs loaded. Cannot match.")
            return ""
            
        for col_name, value in row.items():
            normalized_value = self._normalize_value(value)
            if normalized_value and normalized_value in self.product_ids:
                return normalized_value
        return ""

    async def _process_products(self, sheets: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str]) -> Dict[str, int]:
        reverse_map = {v: k for k, v in column_map.items() if v}
        total_inserted = 0
        total_skipped = 0

        for _, columns, rows in sheets:
            batch, seen = [], set()
            for row in rows:
                pid = str(row.get(column_map.get('product_id', ''), '')).strip().upper()
                if not pid or pid in seen:
                    total_skipped += 1
                    continue

                item = {'product_id': pid, 'supplier_id': self.supplier_id}
                valid_row = True

                for col in columns:
                    db_col = reverse_map.get(col)
                    if db_col:
                        value = self._clean_value(row.get(col), db_col)
                        if value is None and col == column_map.get('product_id', ''):
                            valid_row = False
                            break
                        if value is not None:
                            item[db_col] = value

                if valid_row and len(item) > 2:
                    seen.add(pid)
                    batch.append(item)
                else:
                    total_skipped += 1

                if len(batch) >= self.batch_size:
                    await self._bulk_upsert(Product.__table__, batch, ['product_id'])
                    total_inserted += len(batch)
                    batch.clear()

            if batch:
                await self._bulk_upsert(Product.__table__, batch, ['product_id'])
                total_inserted += len(batch)

        return {"sheets": len(sheets), "rows_inserted": total_inserted, "rows_skipped": total_skipped}

    async def _process_images(self, sheets: List[Tuple[str, List[str], List[Dict[str, Any]]]], image_map: Dict[str, str]) -> Dict[str, int]:
        if not self.product_ids:
            logger.warning("No product IDs loaded. Skipping image processing.")
            return {"sheets": len(sheets), "rows_inserted": 0, "rows_skipped": 0}

        total_inserted = 0
        total_skipped = 0
        
        field_mapping = {}
        for db_field, sheet_column in image_map.items():
            field_mapping[sheet_column] = db_field
        
        logger.info(f"Image field mapping: {field_mapping}")

        for sheet_name, columns, rows in sheets:
            batch = []
            
            relevant_columns = []
            for col in columns:
                if col in field_mapping:
                    relevant_columns.append(col)
                    
            if not relevant_columns:
                logger.info(f"Skipping sheet '{sheet_name}' - no mapped image columns found")
                continue
                
            logger.info(f"Processing image sheet: {sheet_name} with relevant columns: {relevant_columns}")
            
            for row in rows:
                product_id = self._find_product_id_match(row)
                
                if not product_id:
                    total_skipped += 1
                    continue

                image_entry = {"product_id": product_id}
                has_image_data = False

                for col in relevant_columns:
                    db_field = field_mapping.get(col)
                    if db_field and row.get(col):
                        image_entry[db_field] = str(row.get(col)).strip()
                        has_image_data = True

                if has_image_data:
                    batch.append(image_entry)
                    logger.debug(f"Added image entry: {image_entry}")
                else:
                    total_skipped += 1
                    logger.debug(f"Row has matching product_id but no image data")

                if len(batch) >= self.batch_size:
                    await self._bulk_upsert(ProductImage.__table__, batch, ['product_id'])
                    total_inserted += len(batch)
                    batch.clear()

            if batch:
                await self._bulk_upsert(ProductImage.__table__, batch, ['product_id'])
                total_inserted += len(batch)

        logger.info(f"Images: Inserted={total_inserted}, Skipped={total_skipped}")
        return {"sheets": len(sheets), "rows_inserted": total_inserted, "rows_skipped": total_skipped}

    async def _bulk_upsert(self, table: Table, data: List[Dict], conflict_keys: List[str]) -> None:
        if not data:
            return
        
        if table.name == 'product_images':
            for batch in [data[i:i+self.batch_size] for i in range(0, len(data), self.batch_size)]:
                for item in batch:
                    # Check if an entry exists
                    product_id = item.get('product_id')
                    if not product_id:
                        continue                   
                    query = select(ProductImage).where(ProductImage.product_id == product_id)
                    result = await self.db.execute(query)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        update_values = {k: v for k, v in item.items() if k != 'product_id'}
                        stmt = table.update().where(ProductImage.product_id == product_id).values(update_values)
                    else:
                        stmt = table.insert().values(item)
                    
                    await self.db.execute(stmt)
        else:
            update_dict = {k: getattr(pg_insert(table).excluded, k) for k in data[0] if k not in conflict_keys}
            stmt = pg_insert(table).values(data).on_conflict_do_update(
                index_elements=conflict_keys,
                set_=update_dict
            )
            await self.db.execute(stmt)

    def _clean_value(self, val: Any, db_col: str) -> Any:
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return None
        try:
            val_str = str(val).strip()
            if any(x in db_col for x in ['price', 'weight']):
                return float(val_str)
            if any(x in db_col for x in ['qty', 'stock', 'count', 'number']):
                return int(float(val_str))
            if db_col.startswith('is_') or 'active' in db_col:
                return val_str.lower() in ('yes', 'true', '1', 'y')
            if 'date' in db_col or 'time' in db_col or db_col in ('created_at', 'updated_at'):
                date_formats = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S")
                for fmt in date_formats:
                    try:
                        return datetime.strptime(val_str, fmt)
                    except ValueError:
                        continue
                logger.warning(f"Failed to parse date/time for column '{db_col}' with value '{val_str}'")
                return None
            return val_str
        except Exception as ex:
            return None