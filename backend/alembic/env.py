from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import app.models  # noqa: E402, F401  — register all models for autogenerate
from app.core.config import settings  # noqa: E402
from app.models.base import Base  # noqa: E402

target_metadata = Base.metadata

# Override alembic.ini sqlalchemy.url with the value from Pydantic settings
# so DATABASE_URL in .env (or env vars in CI) is the single source of truth.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine.

    asyncpg is an async-only driver — it cannot be used with Alembic's default
    synchronous connection flow. The pattern here is:
      1. Create an async engine via async_engine_from_config.
      2. Open an async connection, then hand it to run_sync(do_run_migrations)
         so Alembic's synchronous migration context can use it transparently.
      3. Dispose the engine to close all pooled connections when done.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
