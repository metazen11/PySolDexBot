from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import Token, PriceData, HolderStats, MomentumScore

class TokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_mint(self, mint_address: str) -> Optional[Token]:
        query = select(Token).where(Token.mint_address == mint_address)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, mint_address: str, **kwargs) -> Token:
        token = Token(mint_address=mint_address, **kwargs)
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def update(self, token: Token, **kwargs) -> Token:
        for key, value in kwargs.items():
            setattr(token, key, value)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_active_tokens(self) -> List[Token]:
        query = select(Token).where(Token.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

class PriceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_price_data(self, token_id: int, price: float, **kwargs) -> PriceData:
        price_data = PriceData(
            token_id=token_id,
            price=price,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        self.session.add(price_data)
        await self.session.commit()
        return price_data

    async def get_price_history(
        self,
        token_id: int,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PriceData]:
        query = select(PriceData).where(PriceData.token_id == token_id)
        
        if start_time:
            query = query.where(PriceData.timestamp >= start_time)
        if end_time:
            query = query.where(PriceData.timestamp <= end_time)
            
        query = query.order_by(desc(PriceData.timestamp)).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_latest_price(self, token_id: int) -> Optional[PriceData]:
        query = select(PriceData).where(
            PriceData.token_id == token_id
        ).order_by(desc(PriceData.timestamp)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

class HolderStatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_holder_stats(self, token_id: int, **kwargs) -> HolderStats:
        stats = HolderStats(
            token_id=token_id,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        self.session.add(stats)
        await self.session.commit()
        return stats

    async def get_latest_stats(self, token_id: int) -> Optional[HolderStats]:
        query = select(HolderStats).where(
            HolderStats.token_id == token_id
        ).order_by(desc(HolderStats.timestamp)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

class MomentumScoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_momentum_score(self, token_id: int, **kwargs) -> MomentumScore:
        score = MomentumScore(
            token_id=token_id,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        self.session.add(score)
        await self.session.commit()
        return score

    async def get_high_momentum_tokens(
        self,
        min_score: float = 0.7,
        min_strength: float = 0.8,
        limit: int = 20
    ) -> List[MomentumScore]:
        query = select(MomentumScore).where(
            and_(
                MomentumScore.total_score >= min_score,
                MomentumScore.signal_strength >= min_strength
            )
        ).order_by(desc(MomentumScore.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()