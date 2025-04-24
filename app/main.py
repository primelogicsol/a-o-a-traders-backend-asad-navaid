from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.version1.route_init import router
from app.core.database import Base, engine
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import os
from starlette.middleware.sessions import SessionMiddleware


load_dotenv()

app=FastAPI()

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