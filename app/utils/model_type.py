from sqlalchemy import Integer, Float, Boolean, String, Date
import pandas as pd
import numpy as np
from datetime import datetime
from app.utils.logger import logger
from app.models.product import Product

def vectorized_type_casting(chunk: pd.DataFrame) -> pd.DataFrame:
    
    type_mapping = {
        column.name: {
            'type': column.type,
            'python_type': column.type.python_type
        } for column in Product.__table__.columns
    }
    
    for col in chunk.columns:
        if col not in type_mapping:
            continue

        col_type = type_mapping[col]['type']
        try:
            chunk[col] = chunk[col].replace(r'^\s*$', None, regex=True) 
            if isinstance(col_type, Integer):
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').astype('Int64')  
            elif isinstance(col_type, Float):
                chunk[col] = chunk[col].replace(r'[\$,%]', '', regex=True)  
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce')  
            elif isinstance(col_type, Boolean):
                chunk[col] = chunk[col].astype(str).str.lower().isin(['true', '1', 'yes', 'y'])  
            elif isinstance(col_type, Date):
                chunk[col] = pd.to_datetime(chunk[col], errors='coerce', utc=True).dt.date 
            elif isinstance(col_type, String):  
                chunk[col] = chunk[col].astype(str) 
            else:
                logger.warning(f"Unsupported column type for column '{col}': {col_type}")
                
        except Exception as e:
            logger.error(f"Error processing column '{col}': {e}")
            chunk[col] = None 

    return chunk
