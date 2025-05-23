from typing import List, Dict, Any, Tuple, Set
from fastapi import HTTPException
from sqlalchemy import Table, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
import logging
from app.models.product import Product
from app.models.product_image import ProductImage
from datetime import datetime, timedelta
import asyncpg

logger = logging.getLogger(__name__)

class BulkInserter:
    def __init__(self, db, supplier_id: int):
        self.db = db
        self.supplier_id = supplier_id
        self.max_parameters = 30000  # PostgreSQL's safe parameter threshold
        self.product_ids: Set[str] = set()
        self.product_id_map = {}  

    async def process_sheets(self, sheets_data: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str], image_map: Dict[str, str]) -> Dict[str, Any]:
        """Enhanced processing with batch-aware ID matching"""
        try:
            # Process products first
            product_sheets, image_sheets = self._classify_sheets(sheets_data, column_map, image_map)
            product_result = await self._process_products(product_sheets, column_map)
            
            # Commit products before loading IDs
            await self.db.commit()
            await self._refresh_product_ids()

            # Process images with full ID visibility
            image_result = await self._process_images(image_sheets, image_map, column_map)
            
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
        # image_map values are the Excel column names we're looking for
        image_cols = set(image_map.values())
        product_sheets, image_sheets = [], []

        for sheet_name, columns, rows in sheets_data:
            # Check for product columns
            if any(c in product_cols for c in columns):
                product_sheets.append((sheet_name, columns, rows))
            
            # ALL sheets are potential image sheets since images could be anywhere
            image_sheets.append((sheet_name, columns, rows))
            
        logger.info(f"Classified sheets - Products: {len(product_sheets)}, Images: {len(image_sheets)} (all sheets)")
        logger.info(f"Looking for image columns (Excel names): {list(image_map.values())}")
        logger.info(f"Looking for product columns (Excel names): {list(product_cols)}")
        return product_sheets, image_sheets

    async def _refresh_product_ids(self):
        """Load product IDs with original casing preservation"""
        result = await self.db.execute(select(Product.product_id).where(Product.supplier_id == self.supplier_id))
        self.product_id_map = {
            self._normalize_value(r[0]): r[0] for r in result if r[0]
        }
        logger.info(f"Loaded {len(self.product_id_map)} product IDs for supplier {self.supplier_id}")
        
        # Debug: Log first few mappings
        if self.product_id_map:
            sample_items = list(self.product_id_map.items())[:5]
            logger.info(f"Sample product ID mappings: {sample_items}")

    def _normalize_value(self, value: Any) -> str:
        """Universal value normalizer for product ID matching"""
        if value is None:
            return ""
        try:
            # Handle numeric values that might be stored as floats
            if isinstance(value, (int, float)):
                if float(value).is_integer():
                    return str(int(value)).strip().upper()
            return str(value).strip().upper()
        except (ValueError, TypeError):
            return str(value).strip().upper()

    async def _process_products(self, sheets: List[Tuple[str, List[str], List[Dict[str, Any]]]], column_map: Dict[str, str]) -> Dict[str, int]:
        reverse_map = {v: k for k, v in column_map.items() if v}
        total_inserted = 0
        total_skipped = 0

        for sheet_name, columns, rows in sheets:
            logger.info(f"Processing product sheet: {sheet_name}")
            
            # Dynamically calculate columns for this sheet
            mapped_columns = [reverse_map[col] for col in columns if col in reverse_map]
            required_columns = {'product_id', 'supplier_id'}
            
            batch = []
            seen_ids = set()

            for row_idx, row in enumerate(rows):
                try:
                    # Normalize product ID
                    raw_pid = row.get(column_map.get('product_id', ''), '')
                    pid = self._normalize_value(raw_pid)
                    
                    if not pid or pid in seen_ids:
                        total_skipped += 1
                        continue

                    # Build item with all potential columns
                    item = {
                        'supplier_id': self.supplier_id,
                        'product_id': pid
                    }
                    valid_row = True

                    # Add all mapped columns with cleaning
                    for col in columns:
                        db_col = reverse_map.get(col)
                        if db_col and db_col not in required_columns:
                            item[db_col] = self._clean_value(row.get(col), db_col)

                    # Validate required fields after cleaning
                    if any(item.get(col) is None for col in required_columns):
                        valid_row = False

                    if valid_row:
                        seen_ids.add(pid)
                        batch.append(item)
                    else:
                        total_skipped += 1

                    # Dynamic batch sizing based on current row's column count
                    if len(batch) >= self._calculate_batch_size(batch):
                        await self._bulk_upsert(Product.__table__, batch, ['product_id', 'supplier_id'])
                        total_inserted += len(batch)
                        batch = []

                except Exception as e:
                    logger.error(f"Row {row_idx} error: {str(e)}")
                    total_skipped += 1

            if batch:
                await self._bulk_upsert(Product.__table__, batch, ['product_id', 'supplier_id'])
                total_inserted += len(batch)

        return {
            "sheets": len(sheets),
            "rows_inserted": total_inserted,
            "rows_skipped": total_skipped
        }

    def _calculate_batch_size(self, current_batch: List[Dict]) -> int:
        """Dynamic batch sizing based on current columns"""
        if not current_batch:
            return 100  # Default fallback
        
        columns_per_row = len(current_batch[0])
        batch_size = max(1, self.max_parameters // columns_per_row)
        logger.debug(f"Dynamic batch size: {batch_size} (columns: {columns_per_row})")
        return batch_size

    async def _bulk_upsert(self, table: Table, data: List[Dict], conflict_keys: List[str]) -> None:
        """Universal bulk upsert with dynamic chunking"""
        if not data:
            return

        # Calculate chunk size based on actual columns
        columns_per_row = len(data[0])
        chunk_size = max(1, self.max_parameters // columns_per_row)

        for chunk in self._chunk_generator(data, chunk_size):
            update_dict = {
                k: getattr(pg_insert(table).excluded, k)
                for k in chunk[0]
                if k not in conflict_keys
            }
            
            stmt = (
                pg_insert(table)
                .values(chunk)
                .on_conflict_do_update(
                    index_elements=conflict_keys,
                    set_=update_dict
                )
            )
            
            try:
                await self.db.execute(stmt)
            except Exception as e:
                logger.error(f"Bulk upsert failed: {str(e)}")
                raise

    def _chunk_generator(self, data: List, size: int):
        """Memory-efficient chunk generator"""
        for i in range(0, len(data), size):
            yield data[i:i + size]

    def _clean_value(self, val: Any, db_col: str) -> Any:
        """Enhanced cleaning with date validation"""
        if val in (None, "", "null", "NULL"):
            return None
            
        try:
            # String normalization
            val_str = str(val).strip()
            
            # Numeric handling
            if any(x in db_col for x in ['price', 'weight']):
                return float(val_str) if val_str else None
                
            if any(x in db_col for x in ['qty', 'stock']):
                return int(float(val_str)) if val_str else None
                
            # Boolean handling
            if db_col.startswith('is_') or 'active' in db_col:
                return val_str.lower() in ('yes', 'true', '1', 'y')
                
            # Date handling
            if 'date' in db_col or 'time' in db_col:
                # Handle Excel serial dates
                if val_str.isdigit():
                    try:
                        base_date = datetime(1899, 12, 30)
                        days = float(val_str)
                        if days > 2958465:  # Prevent unrealistic dates
                            return None
                        parsed = base_date + timedelta(days=days)
                        if parsed.year < 1900:
                            return None
                        return parsed
                    except:
                        pass
                        
                # Normal date parsing
                date_formats = (
                    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
                    "%Y%m%d", "%Y-%m-%d %H:%M:%S"
                )
                for fmt in date_formats:
                    try:
                        parsed = datetime.strptime(val_str, fmt)
                        if parsed.year < 1900:
                            return None
                        return parsed
                    except ValueError:
                        continue
                return None
                
            # Default string handling
            return val_str
        except Exception as e:
            logger.warning(f"Clean error for {db_col}: {val} ({str(e)})")
            return None

    async def _process_images(self, sheets: List[Tuple[str, List[str], List[Dict[str, Any]]]], image_map: Dict[str, str], column_map: Dict[str, str]) -> Dict[str, int]:
     """Image processing with comprehensive product ID matching"""
     total_inserted = 0
     total_skipped = 0
     image_columns = set(image_map.values())  # Excel column names from image map

     for sheet_name, columns, rows in sheets:
        logger.info(f"Processing image sheet: {sheet_name}")
        batch = []
        sheet_image_cols = [col for col in columns if col in image_columns]
        
        if not sheet_image_cols:
            logger.info(f"Skipping sheet {sheet_name} - no image columns found")
            continue

        logger.info(f"Found image columns: {sheet_image_cols}")

        for row_idx, row in enumerate(rows):
            try:
                # Use comprehensive product ID matching
                product_id = self._find_product_id_match(row, column_map.get('product_id', ''))
                if not product_id:
                    logger.debug(f"Row {row_idx} skipped - no product match")
                    total_skipped += 1
                    continue

                # Collect all valid image URLs from this row
                image_urls = []
                for image_col in sheet_image_cols:
                    url = str(row.get(image_col, '')).strip()
                    if url and url.lower() not in ('', 'null', 'nan'):
                        image_urls.append(url)

                if not image_urls:
                    logger.debug(f"Row {row_idx} skipped - no valid URLs")
                    total_skipped += 1
                    continue

                # Create image entries
                batch.extend([{
                    "product_id": product_id,
                    "image_url": url
                } for url in image_urls])

                # Insert in smaller batches for debugging
                if len(batch) >= 100:
                    await self._bulk_upsert(ProductImage.__table__, batch, ['product_id', 'image_url'])
                    total_inserted += len(batch)
                    logger.info(f"Inserted {len(batch)} images from row {row_idx}")
                    batch = []

            except Exception as e:
                logger.error(f"Row {row_idx} error: {str(e)}")
                total_skipped += 1

        if batch:
            await self._bulk_upsert(ProductImage.__table__, batch, ['product_id', 'image_url'])
            total_inserted += len(batch)
            logger.info(f"Inserted final batch of {len(batch)} images")

     return {
        "rows_inserted": total_inserted,
        "rows_skipped": total_skipped,
        "sheets_processed": len(sheets)
    }


    def _find_product_id_match(self, row: Dict[str, Any], product_id_column: str) -> str:
        """Enhanced product ID matching with priority for product_id column"""
        
        # First, try the explicit product_id column
        if product_id_column in row:
            value = row[product_id_column]
            if value:
                normalized = self._normalize_value(value)
                original_id = self.product_id_map.get(normalized)
                if original_id:
                    logger.debug(f"Direct match: {value} -> {normalized} -> {original_id}")
                    return original_id
        
        # Then try all other values in the row
        for col_name, value in row.items():
            if not value or col_name == product_id_column:  # Skip empty values and already-tried product_id column
                continue
                
            normalized = self._normalize_value(value)
            original_id = self.product_id_map.get(normalized)
            
            if original_id:
                logger.debug(f"Indirect match via {col_name}: {value} -> {normalized} -> {original_id}")
                return original_id
        
        return ""