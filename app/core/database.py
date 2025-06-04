from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://avnadmin:AVNS_tWbhwhGpYy3KkIqaapo@aoa-traders-unzilakhan1973-4de3.c.aivencloud.com:19578/defaultdb"
)

# Create async engine with connection pool settings
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Default is 5
    max_overflow=30,     # Default is 10
    pool_timeout=30,
    pool_recycle=3600
)

# Configure session factory
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        yield session