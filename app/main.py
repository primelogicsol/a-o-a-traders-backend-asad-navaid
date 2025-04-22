from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.version1.route_init import api_router
from app.core.database import Base, engine
import asyncio

load_dotenv()

app=FastAPI()

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(api_router)



if __name__ == "__main__":
    asyncio.run(create_db())