import asyncio
from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool

# Add the app folder to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Import your Base and models here
from app.core.database import Base
from app.models import user,product  # import all models here

# This is the Alembic Config object
config = context.config

# Load config file logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata to target for "autogenerate" support
target_metadata = Base.metadata

# Get DB URL from Alembic config (or .env if needed)
def get_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

# Run migrations in offline mode
def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Optional: detect column type changes
    )

    with context.begin_transaction():
        context.run_migrations()

# Run migrations in online mode (Async engine setup)
async def run_migrations_online():
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

# Called by run_migrations_online
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

# Entrypoint
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
