from typing import Optional, List, Dict
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
import pandas as pd

logger = logging.getLogger(__name__)

Base = declarative_base()

# Enhanced token data model with OHLCV
class TokenOHLCV(Base):
    __tablename__ = 'token_ohlcv'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    interval = Column(String, nullable=False)  # '1m', '5m', etc.
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    num_trades = Column(Integer)
    liquidity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class TokenMetadata(Base):
    __tablename__ = 'token_metadata'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String, unique=True, nullable=False, index=True)
    symbol = Column(String)
    name = Column(String)
    decimals = Column(Integer)
    total_supply = Column(Float)
    holder_count = Column(Integer)
    is_active = Column(Boolean, default=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradingOpportunity(Base):
    __tablename__ = 'trading_opportunities'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    highest_price = Column(Float)
    lowest_price = Column(Float)
    safety_score = Column(Float)
    momentum_score = Column(Float)
    volume_24h = Column(Float)
    liquidity = Column(Float)
    market_cap = Column(Float)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    status = Column(String)  # 'watching', 'entered', 'exited', 'blacklisted'
    
class TradeExecution(Base):
    __tablename__ = 'trade_executions'
    
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey('trading_opportunities.id'))
    trade_type = Column(String)  # 'entry', 'take_profit', 'stop_loss', 'trailing_stop'
    amount = Column(Float)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    profit_loss = Column(Float)
    profit_loss_percent = Column(Float)
    notes = Column(String)

class DatabaseHandler:
    def __init__(self, config: Dict):
        self.config = config
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            database_url = self.config['database_url']
            self.engine = create_async_engine(
                database_url,
                echo=self.config.get('sql_echo', False),
                pool_size=self.config.get('pool_size', 5),
                max_overflow=self.config.get('max_overflow', 10)
            )
            
            self.session_factory = sessionmaker(
                self.engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
            
    async def store_ohlcv(self, token_address: str, data: Dict, interval: str = '1m'):
        """Store OHLCV data for a token"""
        async with self.session_factory() as session:
            ohlcv = TokenOHLCV(
                token_address=token_address,
                timestamp=data['timestamp'],
                interval=interval,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume'],
                num_trades=data.get('num_trades'),
                liquidity=data.get('liquidity')
            )
            session.add(ohlcv)
            await session.commit()
            
    async def get_ohlcv(
        self,
        token_address: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = '1m'
    ) -> pd.DataFrame:
        """Get OHLCV data for a token in a specific timeframe"""
        async with self.session_factory() as session:
            query = text("""
                SELECT * FROM token_ohlcv 
                WHERE token_address = :token_address 
                AND timestamp BETWEEN :start_time AND :end_time
                AND interval = :interval
                ORDER BY timestamp ASC
            """)
            
            result = await session.execute(
                query,
                {
                    'token_address': token_address,
                    'start_time': start_time,
                    'end_time': end_time,
                    'interval': interval
                }
            )
            
            rows = result.fetchall()
            if not rows:
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=result.keys())
            df.set_index('timestamp', inplace=True)
            return df
            
    async def update_opportunity(
        self,
        token_address: str,
        current_price: float,
        **kwargs
    ):
        """Update or create trading opportunity"""
        async with self.session_factory() as session:
            # Try to find existing opportunity
            query = text("""
                SELECT * FROM trading_opportunities 
                WHERE token_address = :token_address AND is_active = true
            """)
            result = await session.execute(query, {'token_address': token_address})
            opportunity = result.fetchone()
            
            if opportunity:
                # Update existing
                update_query = text("""
                    UPDATE trading_opportunities 
                    SET current_price = :current_price,
                        highest_price = GREATEST(highest_price, :current_price),
                        lowest_price = LEAST(lowest_price, :current_price),
                        last_updated = :last_updated,
                        safety_score = :safety_score,
                        momentum_score = :momentum_score,
                        volume_24h = :volume_24h,
                        liquidity = :liquidity,
                        market_cap = :market_cap
                    WHERE token_address = :token_address AND is_active = true
                """)
                
                await session.execute(
                    update_query,
                    {
                        'token_address': token_address,
                        'current_price': current_price,
                        'last_updated': datetime.utcnow(),
                        **kwargs
                    }
                )
            else:
                # Create new
                opportunity = TradingOpportunity(
                    token_address=token_address,
                    entry_price=current_price,
                    current_price=current_price,
                    highest_price=current_price,
                    lowest_price=current_price,
                    status='watching',
                    **kwargs
                )
                session.add(opportunity)
                
            await session.commit()
            
    async def record_trade(
        self,
        opportunity_id: int,
        trade_type: str,
        amount: float,
        price: float,
        profit_loss: Optional[float] = None,
        profit_loss_percent: Optional[float] = None,
        notes: Optional[str] = None
    ):
        """Record a trade execution"""
        async with self.session_factory() as session:
            trade = TradeExecution(
                opportunity_id=opportunity_id,
                trade_type=trade_type,
                amount=amount,
                price=price,
                profit_loss=profit_loss,
                profit_loss_percent=profit_loss_percent,
                notes=notes
            )
            session.add(trade)
            await session.commit()
            
    async def get_active_opportunities(self) -> List[Dict]:
        """Get all active trading opportunities"""
        async with self.session_factory() as session:
            query = text("""
                SELECT * FROM trading_opportunities 
                WHERE is_active = true 
                ORDER BY momentum_score DESC
            """)
            result = await session.execute(query)
            return [dict(row) for row in result.fetchall()]
            
    async def blacklist_token(self, token_address: str, reason: str):
        """Blacklist a token"""
        async with self.session_factory() as session:
            await session.execute(
                text("""
                    UPDATE trading_opportunities 
                    SET is_active = false, 
                        status = 'blacklisted',
                        notes = :reason
                    WHERE token_address = :token_address
                """),
                {'token_address': token_address, 'reason': reason}
            )
            await session.commit()

# Create global database handler instance
db_handler = DatabaseHandler({})