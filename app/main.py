from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.version1.route_init import router
from app.core.database import Base, engine
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import os
from starlette.middleware.sessions import SessionMiddleware
from app.utils.embedding import init_embedding_model
from app.core.database import init_db
from contextlib import asynccontextmanager
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowPassword
from fastapi import Security
from fastapi.openapi.utils import get_openapi


load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# {"about-product":"item_description","barcode":"upc_code","cost":"cost_uom","manufacturer-name":"brand_name","minimum-qty":"min_order_qty","brand":"brand_name"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_embedding_model()
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="E-Commerce Platform API",
        version="1.0.0",
        description="This API powers the bulk product upload system with AI mapping.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation.setdefault("security", []).append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from fastapi import FastAPI


app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

app.include_router(router)



if __name__ == "__main__":
    asyncio.run(create_db())