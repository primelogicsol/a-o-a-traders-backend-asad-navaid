from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from app.api.version1.route_init import router
from app.core.database import Base, engine, init_db
from fastapi.openapi.utils import get_openapi

# Load environment variables
load_dotenv()

# Security setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager for application lifespan"""
    await init_db()
    yield

def create_app() -> FastAPI:
    """Factory function for creating the FastAPI application"""
    app = FastAPI(
        title="E-Commerce Platform API",
        version="1.0.0",
        description="API for Bulk Product Upload System with AI Mapping",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }

        # Apply security to all endpoints
        for path in openapi_schema["paths"].values():
            for method in path.values():
                method.setdefault("security", []).append({"BearerAuth": []})

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "default-secret-key"),
        session_cookie="session_cookie"
    )

    # Include routers
    app.include_router(router)

    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile=os.getenv("SSL_KEYFILE", None),
        ssl_certfile=os.getenv("SSL_CERTFILE", None)
    )