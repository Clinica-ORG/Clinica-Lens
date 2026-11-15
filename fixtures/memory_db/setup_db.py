import asyncio
import os

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore


async def main():
    uri = os.environ["DATABASE_URL"]
    async with AsyncPostgresSaver.from_conn_string(uri) as checkpointer:
        await checkpointer.setup()
    async with AsyncPostgresStore.from_conn_string(uri) as store:
        await store.setup()
    print("Memory tables ready")


if __name__ == "__main__":
    asyncio.run(main())