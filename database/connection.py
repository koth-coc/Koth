import os
import asyncpg
import config

_pool: asyncpg.Pool | None = None


async def init_db():
    global _pool
    _pool = await asyncpg.create_pool(dsn=config.DATABASE_URL, min_size=1, max_size=10)

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema_sql = f.read()

    async with _pool.acquire() as con:
        await con.execute(schema_sql)


def pool() -> asyncpg.Pool:
    assert _pool is not None, "database.init_db() must be called before use"
    return _pool
