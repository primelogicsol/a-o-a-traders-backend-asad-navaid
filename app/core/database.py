from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://avnadmin:AVNS_fI2w76wnqMCXtu0y6hu@pg-20bb4070-asadnavaid704-5e20.j.aivencloud.com:27427/defaultdb"
)

engine = create_async_engine(DATABASE_URL, echo=True)


AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
