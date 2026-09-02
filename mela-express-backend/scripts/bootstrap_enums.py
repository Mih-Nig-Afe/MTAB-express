"""Create PostgreSQL enum types required before Alembic migrations (Railway / fresh DB)."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if not url:
        raise SystemExit("DATABASE_URL not set")

    init_sql = Path(__file__).resolve().parent / "init_enums.sql"
    if not init_sql.exists():
        init_sql = Path(__file__).resolve().parents[2] / "docker" / "postgres" / "init.sql"

    sql = init_sql.read_text()
    conn = await asyncpg.connect(url)
    try:
        for stmt in sql.split(";"):
            block = stmt.strip()
            if not block or block.startswith("--") or "CREATE TYPE" not in block.upper():
                continue
            try:
                await conn.execute(block)
                print(f"OK: {block.split(chr(10))[0][:60]}...")
            except asyncpg.DuplicateObjectError:
                print(f"SKIP (exists): {block.split(chr(10))[0][:40]}")
            except Exception as exc:
                print(f"ERR: {exc}")
                raise
    finally:
        await conn.close()
    print("Enum bootstrap complete")


if __name__ == "__main__":
    asyncio.run(main())
