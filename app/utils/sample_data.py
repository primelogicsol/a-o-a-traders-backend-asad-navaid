import asyncio
import math
from typing import Dict, List,Tuple
import concurrent
import pandas as pd
from io import StringIO
from tempfile import SpooledTemporaryFile
from fastapi import UploadFile, HTTPException
import logging


logger = logging.getLogger(__name__)

MAX_CHUNK_SIZE = 1024 * 1024  
MAX_SPOOL_SIZE = 1024 * 1024 * 100 
INSPECTION_ROWS = 1000

async def extract_data(file: UploadFile):
    filename = file.filename.lower()
    logger.info(f"Processing file: {filename}")

    try:
        if filename.endswith(".csv"):
            contents = await file.read()
            text_stream = contents.decode("utf-8", errors="ignore")
            df = pd.read_csv(StringIO(text_stream), nrows=INSPECTION_ROWS)
            return [("CSV", df.columns.tolist(), df.to_dict(orient="records"))]

        elif filename.endswith((".xls", ".xlsx")):
            tmp = SpooledTemporaryFile(max_size=MAX_SPOOL_SIZE)
            while chunk := await file.read(MAX_CHUNK_SIZE):
                tmp.write(chunk)
            tmp.seek(0)

            excel_file = pd.ExcelFile(tmp)
            results = []
            for sheet in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet, nrows=INSPECTION_ROWS)
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
    def _sync_extract(file: UploadFile):
        return asyncio.run(extract_data(file))
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(executor, _sync_extract, file)
            for file in files
        ]
        for file_data in await asyncio.gather(*futures):
            results.extend(file_data)
    return results

def sanitize_row(row: Dict) -> Dict:
    return {k: None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v 
            for k, v in row.items()}

def generate_preview(sheets_data: List[Tuple[str, List[str], List[Dict]]]) -> List[Dict]:
    return [{
        "sheet_name": sheet_name,
        "columns": columns,
        "sample": [sanitize_row(row) for row in rows[:3]]  
    } for sheet_name, columns, rows in sheets_data]
