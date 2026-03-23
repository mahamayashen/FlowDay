from __future__ import annotations

from collections.abc import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
from collections.abc import Callable
from typing import Annotated, ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os  # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException  # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit  # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


def init_engine() -> AsyncEngine:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_init_engine__mutmut_orig, x_init_engine__mutmut_mutants, args, kwargs, None)


def x_init_engine__mutmut_orig() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_1() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = None
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_2() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(None, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_3() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=None)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_4() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_5() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_6() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_7() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = None
    return _engine


def x_init_engine__mutmut_8() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(None, expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_9() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=None)
    return _engine


def x_init_engine__mutmut_10() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(expire_on_commit=False)
    return _engine


def x_init_engine__mutmut_11() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, )
    return _engine


def x_init_engine__mutmut_12() -> AsyncEngine:
    """Create the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=True)
    return _engine

x_init_engine__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_init_engine__mutmut_1': x_init_engine__mutmut_1, 
    'x_init_engine__mutmut_2': x_init_engine__mutmut_2, 
    'x_init_engine__mutmut_3': x_init_engine__mutmut_3, 
    'x_init_engine__mutmut_4': x_init_engine__mutmut_4, 
    'x_init_engine__mutmut_5': x_init_engine__mutmut_5, 
    'x_init_engine__mutmut_6': x_init_engine__mutmut_6, 
    'x_init_engine__mutmut_7': x_init_engine__mutmut_7, 
    'x_init_engine__mutmut_8': x_init_engine__mutmut_8, 
    'x_init_engine__mutmut_9': x_init_engine__mutmut_9, 
    'x_init_engine__mutmut_10': x_init_engine__mutmut_10, 
    'x_init_engine__mutmut_11': x_init_engine__mutmut_11, 
    'x_init_engine__mutmut_12': x_init_engine__mutmut_12
}
x_init_engine__mutmut_orig.__name__ = 'x_init_engine'


async def dispose_engine() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return await _mutmut_trampoline(x_dispose_engine__mutmut_orig, x_dispose_engine__mutmut_mutants, args, kwargs, None)


async def x_dispose_engine__mutmut_orig() -> None:
    """Dispose the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def x_dispose_engine__mutmut_1() -> None:
    """Dispose the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    if _engine is None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def x_dispose_engine__mutmut_2() -> None:
    """Dispose the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = ""
        _session_factory = None


async def x_dispose_engine__mutmut_3() -> None:
    """Dispose the async engine. Called once from the FastAPI lifespan."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = ""

x_dispose_engine__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_dispose_engine__mutmut_1': x_dispose_engine__mutmut_1, 
    'x_dispose_engine__mutmut_2': x_dispose_engine__mutmut_2, 
    'x_dispose_engine__mutmut_3': x_dispose_engine__mutmut_3
}
x_dispose_engine__mutmut_orig.__name__ = 'x_dispose_engine'


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    args = []# type: ignore
    kwargs = {}# type: ignore
    async for i in _mutmut_trampoline(x_get_db__mutmut_orig, x_get_db__mutmut_mutants, args, kwargs, None):
        yield i


async def x_get_db__mutmut_orig() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is None:
        raise RuntimeError("Database engine not initialised. Call init_engine() first.")
    async with _session_factory() as session:
        yield session


async def x_get_db__mutmut_1() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is not None:
        raise RuntimeError("Database engine not initialised. Call init_engine() first.")
    async with _session_factory() as session:
        yield session


async def x_get_db__mutmut_2() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is None:
        raise RuntimeError(None)
    async with _session_factory() as session:
        yield session


async def x_get_db__mutmut_3() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is None:
        raise RuntimeError("XXDatabase engine not initialised. Call init_engine() first.XX")
    async with _session_factory() as session:
        yield session


async def x_get_db__mutmut_4() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is None:
        raise RuntimeError("database engine not initialised. call init_engine() first.")
    async with _session_factory() as session:
        yield session


async def x_get_db__mutmut_5() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for use as a FastAPI dependency.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    if _session_factory is None:
        raise RuntimeError("DATABASE ENGINE NOT INITIALISED. CALL INIT_ENGINE() FIRST.")
    async with _session_factory() as session:
        yield session

x_get_db__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_get_db__mutmut_1': x_get_db__mutmut_1, 
    'x_get_db__mutmut_2': x_get_db__mutmut_2, 
    'x_get_db__mutmut_3': x_get_db__mutmut_3, 
    'x_get_db__mutmut_4': x_get_db__mutmut_4, 
    'x_get_db__mutmut_5': x_get_db__mutmut_5
}
x_get_db__mutmut_orig.__name__ = 'x_get_db'
