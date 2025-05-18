from typing import List
import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth.auth import UserResponse
from app.core.role import role_required
from app.models.product import Product
from app.services.ai_mapping.column_mapping import generate_column_mapping
from app.services.ai_mapping.image_mapping import generate_image_mapping
from app.utils.sample_data import data_extraction, generate_preview
import logging
from app.services.product.product_insertion import BulkInserter

logger = logging.getLogger(__name__)
router = APIRouter()



@router.post("/upload-and-process")
async def upload_process(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(role_required("supplier"))
) -> JSONResponse:
    try:
        supplier_id = user.id
        logger.info(f"Processing upload for supplier ID: {supplier_id}")

        sheets_data = await data_extraction(files)
        all_sheet_preview = generate_preview(sheets_data)

        column_map, image_map = await asyncio.gather(
            generate_column_mapping(
                all_sheet_preview=all_sheet_preview,
                db_fields=Product.__table__.columns.keys()
            ),
            generate_image_mapping(all_sheet_preview=all_sheet_preview)
        )

        inserter = BulkInserter(db, supplier_id)
        insert_results = await inserter.process_sheets(sheets_data, column_map, image_map)

        return JSONResponse(content={
            "column_mapping": column_map,
            "image_mapping": image_map,
            "result":insert_results
        })

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))