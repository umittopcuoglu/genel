import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Alembic yapılandırması
config = context.config
fileConfig(config.config_file_name)

# Modelleri import et (Base'leri topla)
from app.core.db import Base
from app.models.base import BaseModel
from app.models.user import User, RefreshToken
from app.models.audit import AuditLog
from app.models.front_office import RoomType, Room, Guest, Reservation, Stay, Trace
from app.models.reservation_ext import RatePlan, Availability
from app.models.finance import Folio, FolioItem, Payment, NightAuditRun
from app.models.housekeeping import HousekeepingTask, LostFound, MinibarItem
from app.models.finance import Folio, FolioItem, Payment, NightAuditRun
from app.models.housekeeping import HousekeepingTask, LostFound, MinibarItem
from app.models.finance import Folio, FolioItem, Payment, NightAuditRun
from app.models.housekeeping import HousekeepingTask, LostFound, MinibarItem

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Offline migration çalıştırma."""
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
    """Asenkron migration çalıştırma."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    """Online migration çalıştırma."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
