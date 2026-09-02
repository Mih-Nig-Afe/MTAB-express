"""Reset Railway Postgres schema for a clean migration run."""
import asyncio
import os
import asyncpg

async def main():
    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(url)
    await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    await conn.close()
    print("Schema reset OK")

asyncio.run(main())
