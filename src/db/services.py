from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .repositories import TokenRepository, PriceRepository, HolderStatsRepository, MomentumScoreRepository
from .models import Token, PriceData, HolderStats, MomentumScore

class TokenService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.token_repo = TokenRepository(session)
        self.price_repo = PriceRepository(session)
        self.holder_repo = HolderStatsRepository(session)
        self.momentum_repo = MomentumScoreRepository(session)

    async def process_price_update(
        self, 
        mint_address: str, 
        price: float,
        metadata: Dict,
        **kwargs
    ) -> PriceData:
        """Process price update, creating token if needed"""
        token = await self.token_repo.get_by_mint(mint_address)
        
        if not token:
            token = await self.token_repo.create(
                mint_address=mint_address,
                symbol=metadata.get('symbol'),
                name=metadata.get('name'),
                decimals=metadata.get('decimals', 9)
            )
        
        return await self.price_repo.add_price_data(
            token_id=token.id,
            price=price,
            **kwargs
        )

    async def update_holder_stats(
        self,
        mint_address: str,
        total_holders: int,
        **kwargs
    ) -> HolderStats:
        """Update holder statistics for token"""
        token = await self.token_repo.get_by_mint(mint_address)
        if not token:
            raise ValueError(f"Token not found: {mint_address}")
            
        return await self.holder_repo.add_holder_stats(
            token_id=token.id,
            total_holders=total_holders,
            **kwargs
        )

    async def update_momentum_score(
        self,
        mint_address: str,
        total_score: float,
        **kwargs
    ) -> MomentumScore:
        """Update momentum score for token"""
        token = await self.token_repo.get_by_mint(mint_address)
        if not token:
            raise ValueError(f"Token not found: {mint_address}")
            
        return await self.momentum_repo.add_momentum_score(
            token_id=token.id,
            total_score=total_score,
            **kwargs
        )

    async def get_token_price_history(
        self,
        mint_address: str,
        hours: int = 24
    ) -> List[PriceData]:
        """Get price history for token"""
        token = await self.token_repo.get_by_mint(mint_address)
        if not token:
            return []
            
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return await self.price_repo.get_price_history(
            token_id=token.id,
            start_time=start_time
        )
        
    async def get_latest_price(
        self,
        mint_address: str
    ) -> Optional[PriceData]:
        """Get latest price for token"""
        token = await self.token_repo.get_by_mint(mint_address)
        if not token:
            return None
            
        return await self.price_repo.get_latest_price(token.id)
        
    async def get_latest_holder_stats(
        self,
        mint_address: str
    ) -> Optional[HolderStats]:
        """Get latest holder stats for token"""
        token = await self.token_repo.get_by_mint(mint_address)
        if not token:
            return None
            
        return await self.holder_repo.get_latest_stats(token.id)
        
    async def get_high_momentum_tokens(
        self,
        min_score: float = 0.7,
        min_strength: float = 0.8,
        limit: int = 20
    ) -> List[Dict]:
        """Get tokens with high momentum scores"""
        scores = await self.momentum_repo.get_high_momentum_tokens(
            min_score=min_score,
            min_strength=min_strength,
            limit=limit
        )
        
        results = []
        for score in scores:
            token = await self.token_repo.get_by_mint(score.token.mint_address)
            if token:
                results.append({
                    'mint_address': token.mint_address,
                    'symbol': token.symbol,
                    'name': token.name,
                    'score': score.total_score,
                    'strength': score.signal_strength,
                    'timestamp': score.timestamp
                })
                
        return results
