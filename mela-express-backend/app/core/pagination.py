from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

T = TypeVar('T')

class PaginationParams:
    def __init__(self, page: int = 1, size: int = 20):
        self.page = max(1, page)
        self.size = min(100, max(1, size))

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

async def paginate(query, db: AsyncSession, page: int, size: int) -> tuple[Sequence, int]:
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    
    items_query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    return items, total_count
