import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool, StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./devflow.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    **({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    } if _is_sqlite else {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "poolclass": QueuePool,
    })
)
