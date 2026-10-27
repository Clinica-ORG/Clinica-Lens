import os
import asyncpg
import sqlglot
from sqlglot import exp

from app.core.config import Settings

pool: asyncpg.Pool | None = None
MAX_ROWS = 200

async def init_pool(settings: Settings) -> None:
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.PG_DB_URL,
        min_size=1, max_size=5,
        command_timeout=10,
        statement_cache_size=0,
    )

async def close_pool() -> None:
    if pool:
        await pool.close()

def validate_select(sql: str) -> str:
    """Allow exactly one read-only statement. Returns normalized SQL."""
    try:
        stmts = [s for s in sqlglot.parse(sql, read="postgres") if s]
    except sqlglot.errors.ParseError:
        raise ValueError("Invalid SQL syntax.")
    if len(stmts) != 1:
        raise ValueError("Exactly one statement is allowed.")
    stmt = stmts[0]
    if not isinstance(stmt, (exp.Select, exp.Union)):
        raise ValueError("Only SELECT queries are allowed.")
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter)
    if any(stmt.find(t) for t in forbidden):
        raise ValueError("Write operations are not allowed.")
    return stmt.sql(dialect="postgres")

async def fetch_readonly(sql: str, *args) -> list[dict]:
    async with pool.acquire() as con:
        async with con.transaction(readonly=True):
            rows = await con.fetch(sql, *args)
    return [dict(r) for r in rows]

async def run_select(sql: str) -> list[dict]:
    clean = validate_select(sql)
    return await fetch_readonly(f"select * from ({clean}) q limit {MAX_ROWS}")