from typing import List, Dict, Any, Tuple, Set, Optional
from datetime import datetime, timedelta
from sqlalchemy import Table, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi import HTTPException
import time
import re
from app.models.product_image import ProductImage

class BulkInserter:
    def __init__(self, db, supplier_id: int):
        self.db = db
        self.supplier_id = supplier_id
        self.batch_size = 5000
        self.image_batch_size = 2000
        self.max_parameters = 30000
        self.product_ids: Set[str] = set()
        self.product_id_mapping: Dict[str, str] = {}
        self.debug_stats = {
            'total_rows_processed': 0,
            'products_processed': 0,
            'images_processed': 0,
            'processing_start_time': None,
            'products_start_time': None,
            'images_start_time': None
        }

    async def process_sheets(self, sheets_data: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str], image_map: Dict[str, str]) -> Dict[str, Any]:
        self.debug_stats['processing_start_time'] = time.time()
        try:
            product_sheets, image_sheets = self._classify_sheets(sheets_data, column_map, image_map)
            self.debug_stats['products_start_time'] = time.time()
            product_result = await self._process_products(product_sheets, column_map)
            products_time = time.time() - self.debug_stats['products_start_time']
            await self._refresh_product_ids_enhanced()
            self.debug_stats['images_start_time'] = time.time()
            image_result = await self._process_images_enhanced(image_sheets, image_map)
            images_time = time.time() - self.debug_stats['images_start_time']
            total_time = time.time() - self.debug_stats['processing_start_time']
            return {
                "products": product_result,
                "images": image_result,
                "debug_stats": {
                    "total_time": total_time,
                    "products_time": products_time,
                    "images_time": images_time,
                    "total_rows": self.debug_stats['total_rows_processed']
                }
            }
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Bulk insert failed: {str(e)}")
        finally:
            await self.db.commit()

    def _classify_sheets(self, sheets_data: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str], image_map: Dict[str, str]) -> Tuple[List, List]:
        product_cols = set(column_map.values())
        product_sheets, image_sheets = [], []
        for sheet_name, columns, rows in sheets_data:
            self.debug_stats['total_rows_processed'] += len(rows)
            if any(c in product_cols for c in columns):
                product_sheets.append((sheet_name, columns, rows))
            image_sheets.append((sheet_name, columns, rows))
        return product_sheets, image_sheets

    async def _refresh_product_ids_enhanced(self):
        from app.models.product import Product
        result = await self.db.execute(
            select(Product.product_id).where(Product.supplier_id == self.supplier_id)
        )
        product_ids = result.scalars().all()
        self.product_ids = set()
        self.product_id_mapping = {}
        for original_id in product_ids:
            if original_id is not None:
                original_id = str(original_id)
                for variant in self._normalize_value_enhanced(original_id):
                    self.product_ids.add(variant)
                    self.product_id_mapping[variant] = original_id

    def _normalize_value_enhanced(self, value: Any) -> List[str]:
        if value is None:
            return []
        try:
            variants = []
            str_val = str(value).strip()
            if not str_val:
                return []
            variants.extend([str_val, str_val.upper(), str_val.lower()])
            try:
                if str_val.replace('.', '').replace('-', '').replace('_', '').isdigit():
                    float_val = float(str_val)
                    if float_val.is_integer():
                        clean_num = str(int(float_val))
                        variants.extend([clean_num, clean_num.upper(), clean_num.lower()])
                    clean_no_zeros = str_val.lstrip('0') or '0'
                    variants.extend([clean_no_zeros, clean_no_zeros.upper(), clean_no_zeros.lower()])
            except (ValueError, TypeError):
                pass
            clean_val = re.sub(r'\s+', '', str_val)
            if clean_val != str_val:
                variants.extend([clean_val, clean_val.upper(), clean_val.lower()])
            unique_variants = []
            seen = set()
            for v in variants:
                if v and v not in seen:
                    unique_variants.append(v)
                    seen.add(v)
            return unique_variants
        except Exception:
            return [str(value)] if value else []

    async def _process_products(self, sheets: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str]) -> Dict[str, int]:
        from app.models.product import Product
        reverse_map = {v: k for k, v in column_map.items() if v}
        total_inserted = 0
        total_skipped = 0
        for sheet_name, columns, rows in sheets:
            batch = []
            seen_ids = set()
            sheet_inserted = 0
            sheet_skipped = 0
            for row in rows:
                try:
                    raw_pid = row.get(column_map.get('product_id', ''), '')
                    pid = self._normalize_value(raw_pid)
                    if not pid or pid in seen_ids:
                        total_skipped += 1
                        sheet_skipped += 1
                        continue
                    item = {'supplier_id': self.supplier_id, 'product_id': pid}
                    valid_row = True
                    for col in columns:
                        db_col = reverse_map.get(col)
                        if db_col and db_col not in {'product_id', 'supplier_id'}:
                            item[db_col] = self._clean_value(row.get(col), db_col)
                    if any(item.get(col) is None for col in ['product_id', 'supplier_id']):
                        valid_row = False
                    if valid_row:
                        seen_ids.add(pid)
                        batch.append(item)
                    else:
                        total_skipped += 1
                        sheet_skipped += 1
                    if len(batch) >= self._calculate_batch_size(batch):
                        await self._bulk_upsert(Product.__table__, batch, ['product_id'])
                        total_inserted += len(batch)
                        sheet_inserted += len(batch)
                        batch = []
                except Exception:
                    total_skipped += 1
                    sheet_skipped += 1
            if batch:
                await self._bulk_upsert(Product.__table__, batch, ['product_id'])
                total_inserted += len(batch)
                sheet_inserted += len(batch)
        self.debug_stats['products_processed'] = total_inserted
        return {
            "sheets": len(sheets),
            "rows_inserted": total_inserted,
            "rows_skipped": total_skipped
        }

    def _calculate_batch_size(self, current_batch: List[Dict]) -> int:
        if not current_batch:
            return 100
        columns_per_row = len(current_batch[0])
        batch_size = max(1, self.max_parameters // columns_per_row)
        return min(batch_size, 500)

    async def _bulk_upsert(self, table: Table, data: List[Dict], conflict_keys: List[str]) -> None:
        if not data:
            return
        insert_stmt = pg_insert(table).values(data)
        update_cols = [col for col in data[0].keys() if col not in conflict_keys]
        update_dict = {col: getattr(insert_stmt.excluded, col) for col in update_cols}
        stmt = insert_stmt.on_conflict_do_update(index_elements=conflict_keys, set_=update_dict)
        await self.db.execute(stmt)

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

    def _clean_value(self, val: Any, db_col: str) -> Any:
        if val in (None, "", "null", "NULL"):
            return None
        try:
            val_str = str(val).strip()
            if any(x in db_col for x in ['price', 'weight']):
                return float(val_str) if val_str else None
            if any(x in db_col for x in ['qty', 'stock']):
                return int(float(val_str)) if val_str else None
            if db_col.startswith('is_') or 'active' in db_col:
                return val_str.lower() in ('yes', 'true', '1', 'y')
            if 'date' in db_col or 'time' in db_col:
                if val_str.isdigit():
                    try:
                        base_date = datetime(1899, 12, 30)
                        days = float(val_str)
                        if days > 2958465:
                            return None
                        parsed = base_date + timedelta(days=days)
                        if parsed.year < 1900:
                            return None
                        return parsed
                    except:
                        pass
                date_formats = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d", "%Y-%m-%d %H:%M:%S")
                for fmt in date_formats:
                    try:
                        parsed = datetime.strptime(val_str, fmt)
                        if parsed.year < 1900:
                            return None
                        return parsed
                    except ValueError:
                        continue
                return None
            return val_str
        except Exception:
            return None

    async def _process_images_enhanced(self, sheets: List[Tuple[str, List[str], List[Dict[str, Any]]]], image_map: Dict[str, str]) -> Dict[str, int]:
        if not self.product_ids:
            return {"sheets": len(sheets), "rows_inserted": 0, "rows_skipped": 0}
        total_inserted = 0
        total_skipped = 0
        sheet_to_db_map = {v: k for k, v in image_map.items()}
        for sheet_name, columns, rows in sheets:
            batch = []
            available_mappings = {col: sheet_to_db_map[col] for col in columns if col in sheet_to_db_map}
            if not available_mappings:
                total_skipped += len(rows)
                continue
            for row in rows:
                matched_id = self._find_product_id_in_row(row)
                if not matched_id:
                    total_skipped += 1
                    continue
                image_entry = {"product_id": matched_id}
                has_image_data = False
                for sheet_col, db_field in available_mappings.items():
                    if sheet_col in row and row[sheet_col]:
                        cleaned_value = str(row[sheet_col]).strip()
                        if cleaned_value:
                            image_entry[db_field] = cleaned_value
                            has_image_data = True
                if has_image_data:
                    batch.append(image_entry)
                else:
                    total_skipped += 1
                if len(batch) >= self.image_batch_size:
                    inserted = await self._bulk_insert_images(batch)
                    total_inserted += inserted
                    batch = []
            if batch:
                inserted = await self._bulk_insert_images(batch)
                total_inserted += inserted
        return {
            "sheets": len(sheets), 
            "rows_inserted": total_inserted, 
            "rows_skipped": total_skipped
        }

    async def _bulk_insert_images(self, batch: List[Dict]) -> int:
        if not batch:
            return 0
        try:
            await self._bulkimage_upsert(ProductImage.__table__, batch)
            return len(batch)
        except Exception:
            return 0

    def _find_product_id_in_row(self, row: Dict[str, Any]) -> Optional[str]:
        for value in row.values():
            if not value:
                continue
            for variant in self._normalize_value_enhanced(value):
                if variant in self.product_ids:
                    return self.product_id_mapping[variant]
        return None

    async def _bulkimage_upsert(self, table: Table, data: List[Dict]) -> None:
        if not data:
            return
        conflict_keys = [col.name for col in table.primary_key.columns]
        update_cols = [col for col in data[0].keys() if col not in conflict_keys]
        update_dict = {col: getattr(pg_insert(table).excluded, col) for col in update_cols}
        stmt = pg_insert(table).values(data).on_conflict_do_update(index_elements=conflict_keys, set_=update_dict)
        await self.db.execute(stmt)