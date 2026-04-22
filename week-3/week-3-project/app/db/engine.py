from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import(
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
    AsyncEngine)
from app.core.config import setting



def _build_engine(url: str, pool_size: int, max_overflow: int) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )


# ── App engine ────────────────────────────────────────────────────────

_app_engine: AsyncEngine | None = None


def get_app_engine() -> AsyncEngine:
    global _app_engine
    if _app_engine is None:
        _app_engine = _build_engine(
            url=setting.APP_DATABASE_URL,
            pool_size=20,
            max_overflow=10,
        )
    return _app_engine


# ── Checkpoint engine ─────────────────────────────────────────────────

_checkpoint_engine: AsyncEngine | None = None


def _checkpoint_dsn() -> str:
    return setting.CHECKPOINT_CONN_STRING or setting.CHECKPOINT_DATABASE_URL


def get_checkpoint_engine() -> AsyncEngine:
    global _checkpoint_engine
    if _checkpoint_engine is None:
        _checkpoint_engine = _build_engine(
            url=_checkpoint_dsn(),
            pool_size=5,
            max_overflow=3,
        )
    return _checkpoint_engine


def _to_psycopg_conninfo(async_url: str) -> str:
    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return async_url


_checkpoint_pool: AsyncConnectionPool | None = None


def get_checkpoint_pool() -> AsyncConnectionPool:
    global _checkpoint_pool
    if _checkpoint_pool is None:
        _checkpoint_pool = AsyncConnectionPool(
            conninfo=_to_psycopg_conninfo(_checkpoint_dsn()),
            min_size=1,
            max_size=5,
            open=False,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
            },
        )
    return _checkpoint_pool


_session_factory: async_sessionmaker | None = None


def get_session_factory() -> async_sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_app_engine(),      # lazy — engine created here if needed
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session():
    """FastAPI dependency — yields one session per request."""
    async with get_session_factory()() as session:
        yield session