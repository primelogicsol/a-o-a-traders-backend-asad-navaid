from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
import numpy as np
from sqlalchemy import insert
import pandas as pd 
from app.utils.model_type import vectorized_type_casting


async def batch_insert(db: AsyncSession, chunk: pd.DataFrame):
    chunk = vectorized_type_casting(chunk)
    chunk = chunk.replace({np.nan: None})
    for col in chunk.columns:
     if pd.api.types.is_bool_dtype(chunk[col]):
        chunk[col] = chunk[col].astype(object)
        chunk[col] = chunk[col].where(chunk[col].notna(), None)
    
    records = chunk.to_dict(orient="records")
    await db.execute(insert(Product).values(records))
    await db.commit()
