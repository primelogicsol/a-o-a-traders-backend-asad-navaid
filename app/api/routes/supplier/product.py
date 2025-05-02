from fastapi import APIRouter, UploadFile, Depends, HTTPException, File,Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from io import StringIO
from app.core.database import get_db
from app.utils.logger import logger
import json
from app.services.ai_mapping.column_mapping import vectorized_column_mapping
from app.utils.model_type import vectorized_type_casting
from app.utils.embedding import init_embedding_model
from app.crud.product_crud import batch_insert
from app.models.product import Product
from app.services.auth.jwt import get_current_user
from app.schemas.auth.auth import UserResponse
from app.core.role import role_required


router = APIRouter()

CHUNK_SIZE = 10_000
BATCH_SIZE = 500

@router.post("/upload-file/")
async def upload_file(db: AsyncSession = Depends(get_db), file: UploadFile = File(...)
                      ,current_user: UserResponse = Depends(role_required("supplier")) ):
    try:
        csv_stream = StringIO()
        while content := await file.read(1024 * 1024):  
            csv_stream.write(content.decode())
        
        csv_stream.seek(0)
        df_chunk = pd.read_csv(csv_stream, nrows=100)  
        column_mapping = vectorized_column_mapping(df_chunk.columns.tolist())
        
        return JSONResponse(content={
            "message": "Column mapping suggestions.",
            "suggested_mappings": column_mapping
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    

@router.post("/finalize-mapping/")
async def finalize_mapping(
    file: UploadFile = File(...),
    mappings: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("supplier")) 
):
    try:
        if current_user is None or current_user.role != "supplier":
            raise HTTPException(status_code=403, detail="Only suppliers can upload data")
        mappings = json.loads(mappings)
        
        csv_stream = StringIO()
        while content := await file.read(1024 * 1024):
            csv_stream.write(content.decode())
        csv_stream.seek(0)
        
        for chunk in pd.read_csv(csv_stream, chunksize=CHUNK_SIZE):
            chunk = chunk.rename(columns=mappings)
            chunk = vectorized_type_casting(chunk)
            chunk['supplier_id'] = current_user.id
            valid_columns = Product.__table__.columns.keys()
            chunk = chunk[[c for c in chunk.columns if c in valid_columns]]  
            
            
            for batch in range(0, len(chunk), BATCH_SIZE):
                await batch_insert(db, chunk.iloc[batch:batch+BATCH_SIZE])
        
        return JSONResponse(content={"message": "Data successfully inserted"})

    except Exception as e:
        await db.rollback()
        logger.error(f"Insertion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insertion failed: {str(e)}")