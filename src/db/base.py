from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine

Base = declarative_base()

class AsyncDatabaseSession:
    def __init__(self):
        self._session: AsyncSession | None = None
        self._engine: AsyncEngine | None = None

    def init(self, db_url: str) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=True,
            future=True
        )
        self._session = sessionmaker(
            self._engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )()

    @property
    def session(self) -> AsyncSession:
        return self._session

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

db = AsyncDatabaseSession()