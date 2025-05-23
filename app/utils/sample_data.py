import asyncio
import math
from typing import Dict, List,Tuple
import concurrent
import pandas as pd
from io import StringIO
from tempfile import SpooledTemporaryFile
from fastapi import UploadFile, HTTPException
import logging
import os


logger = logging.getLogger(__name__)

MAX_CHUNK_SIZE = 1024 * 1024  # 1MB
MAX_SPOOL_SIZE = 1024 * 1024 * 100  # 100MB
INSPECTION_ROWS = 30000
MAX_WORKERS = min(os.cpu_count() or 4, 8) 

async def extract_data(file: UploadFile):
    """Extract data from uploaded files with improved performance"""
    filename = file.filename.lower()
    logger.info(f"Processing file: {filename}")
    
    try:
        if filename.endswith(".csv"):
            # Read CSV file with optimized settings
            contents = await file.read()
            text_stream = contents.decode("utf-8", errors="ignore")
            
            # Use more efficient CSV reading options
            df = pd.read_csv(
                StringIO(text_stream), 
                nrows=INSPECTION_ROWS, 
                low_memory=True,
                on_bad_lines='skip',  # Skip bad lines instead of failing
                engine='c'  # Use C engine for better performance
            )
            return [("CSV", df.columns.tolist(), df.to_dict(orient="records"))]
            
        elif filename.endswith((".xls", ".xlsx")):
            # Efficiently read Excel file
            tmp = SpooledTemporaryFile(max_size=MAX_SPOOL_SIZE)
            # Read in larger chunks for better performance
            while chunk := await file.read(MAX_CHUNK_SIZE):
                tmp.write(chunk)
            tmp.seek(0)
            
            excel_file = pd.ExcelFile(tmp)
            results = []
            
            # Process Excel sheets with optimized settings
            for sheet in excel_file.sheet_names:
                try:
                    df = pd.read_excel(
                        excel_file, 
                        sheet_name=sheet, 
                        nrows=INSPECTION_ROWS,
                        engine='openpyxl' if filename.endswith('.xlsx') else 'xlrd',
                        na_filter=False  # Don't convert empty strings to NaN
                    )
                    if not df.empty:
                        results.append((sheet, df.columns.tolist(), df.to_dict(orient="records")))
                    else:
                        logger.warning(f"Sheet '{sheet}' is empty or unreadable.")
                except Exception as sheet_err:
                    logger.error(f"Error reading sheet '{sheet}': {sheet_err}")
            
            return results
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
            
    except Exception as e:
        logger.error(f"Failed to extract data from {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error extracting file content.")

async def data_extraction(files: List[UploadFile]):
    """Process multiple files concurrently with improved threading strategy"""
    # Use a separate function that can be pickled for ProcessPoolExecutor
    def _process_file(file):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(extract_data(file))
        finally:
            loop.close()
    
    results = []
    
    # Use ThreadPoolExecutor for better I/O parallelism with uploaded files
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all file processing tasks
        future_to_file = {executor.submit(_process_file, file): file for file in files}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                file_data = future.result()
                results.extend(file_data)
                logger.info(f"Successfully processed {file.filename}")
            except Exception as exc:
                logger.error(f"File {file.filename} generated an exception: {exc}")
    
    return results

def sanitize_row(row: Dict) -> Dict:
    """Sanitize row data, handling NaN and infinite values"""
    # More comprehensive sanitization
    sanitized = {}
    for k, v in row.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            sanitized[k] = None
        elif v == "" or v == "null" or v == "NULL":  # Handle empty strings and null values
            sanitized[k] = None
        else:
            sanitized[k] = v
    return sanitized

def generate_preview(sheets_data: List[Tuple[str, List[str], List[Dict]]]) -> List[Dict]:
    """Generate preview of sheet data with improved sanitization"""
    preview = []
    for sheet_name, columns, rows in sheets_data:
        # Only include non-empty samples
        sample_rows = []
        sample_count = 0
        
        for row in rows:
            if sample_count >= 3:
                break
                
            sanitized_row = sanitize_row(row)
            # Check if row has actual data (not all nulls)
            if any(v is not None for v in sanitized_row.values()):
                sample_rows.append(sanitized_row)
                sample_count += 1
        
        preview.append({
            "sheet_name": sheet_name,
            "columns": columns,
            "sample": sample_rows
        })
    
    return preview

# MAX_CHUNK_SIZE = 1024 * 1024  
# MAX_SPOOL_SIZE = 1024 * 1024 * 100 
# INSPECTION_ROWS = 1000

# async def extract_data(file: UploadFile):
#     filename = file.filename.lower()
#     logger.info(f"Processing file: {filename}")

#     try:
#         if filename.endswith(".csv"):
#             contents = await file.read()
#             text_stream = contents.decode("utf-8", errors="ignore")
#             df = pd.read_csv(StringIO(text_stream), nrows=INSPECTION_ROWS)
#             return [("CSV", df.columns.tolist(), df.to_dict(orient="records"))]

#         elif filename.endswith((".xls", ".xlsx")):
#             tmp = SpooledTemporaryFile(max_size=MAX_SPOOL_SIZE)
#             while chunk := await file.read(MAX_CHUNK_SIZE):
#                 tmp.write(chunk)
#             tmp.seek(0)

#             excel_file = pd.ExcelFile(tmp)
#             results = []
#             for sheet in excel_file.sheet_names:
#                 try:
#                     df = pd.read_excel(excel_file, sheet_name=sheet, nrows=INSPECTION_ROWS)
#                     if not df.empty:
#                         results.append((sheet, df.columns.tolist(), df.to_dict(orient="records")))
#                     else:
#                         logger.warning(f"Sheet '{sheet}' is empty or unreadable.")
#                 except Exception as sheet_err:
#                     logger.error(f"Error reading sheet '{sheet}': {sheet_err}")

#             return results

#         else:
#             raise HTTPException(status_code=400, detail="Unsupported file format.")

#     except Exception as e:
#         logger.error(f"Failed to extract data from {filename}: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Error extracting file content.")



# async def data_extraction(files: List[UploadFile]):
#     def _sync_extract(file: UploadFile):
#         return asyncio.run(extract_data(file))
    
#     results = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
#         loop = asyncio.get_event_loop()
#         futures = [
#             loop.run_in_executor(executor, _sync_extract, file)
#             for file in files
#         ]
#         for file_data in await asyncio.gather(*futures):
#             results.extend(file_data)
#     return results

# def sanitize_row(row: Dict) -> Dict:
#     return {k: None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v 
#             for k, v in row.items()}

# def generate_preview(sheets_data: List[Tuple[str, List[str], List[Dict]]]) -> List[Dict]:
#     return [{
#         "sheet_name": sheet_name,
#         "columns": columns,
#         "sample": [sanitize_row(row) for row in rows[:3]]  
#     } for sheet_name, columns, rows in sheets_data]
