import time
import logging
from langchain_core.tools import tool
from app.db.database import fetch_readonly, run_select

log = logging.getLogger("agent.tools")


@tool
async def list_tables() -> list[str]:
    """List the tables of the clinical schema. Call it first if need to query Database, then describe_table."""
    rows = await fetch_readonly(
        "select table_name from information_schema.tables "
        "where table_schema = 'clinical' order by table_name"
    )
    return [r["table_name"] for r in rows]


@tool
async def describe_table(table: str) -> list[dict]:
    """Show the columns of one table and 3 sample rows. Call it before writing SQL on that table."""
    desc = await fetch_readonly(
        "select column_name, data_type from information_schema.columns "
        "where table_schema = 'clinical' and table_name = $1 "
        "order by ordinal_position "
        "limit 3",
        table,
    )
    columns = [{"name": r["column_name"], "type": r["data_type"]} for r in desc]
    _samples = await fetch_readonly(f"select * from clinical.{table} limit 3")
    samples = [dict(s) for s in _samples]
    return {"table": table, "columns": columns, "sample_rows": samples}


@tool
async def query_db(sql: str) -> list[dict] | str:
    """Run ONE read-only SELECT.
    Tables are in the `clinical` schema and need to be referenced as clinical.<table>
    Max 200 rows are returned."""
    started, status = time.monotonic(), "error"
    try:
        result = await run_select(sql)
        status = "ok"
        return result
    except ValueError as e:
        status = "rejected"
        return f"Query rejected: {e}"
    except Exception:
        log.exception("query failed")
        return "The query failed. Check the table and column names and try again."
    finally:
        log.info(
            "query_db status=%s ms=%d sql=%r",
            status,
            (time.monotonic() - started) * 1000,
            sql,
        )


def get_db_tools():
    "Get list of tools"
    # used same global pool during lifespan so no need to nest them
    return [list_tables, describe_table, query_db]
