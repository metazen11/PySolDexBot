from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    mint_address = Column(String, unique=True, nullable=False, index=True)
    symbol = Column(String)
    name = Column(String)
    decimals = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    prices = relationship("PriceData", back_populates="token", cascade="all, delete-orphan")
    holder_stats = relationship("HolderStats", back_populates="token", cascade="all, delete-orphan")
    momentum_scores = relationship("MomentumScore", back_populates="token", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Token(mint_address='{self.mint_address}', symbol='{self.symbol}')>"

class PriceData(Base):
    __tablename__ = 'price_data'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume_24h = Column(Float)
    liquidity = Column(Float)
    price_change_24h = Column(Float)
    volume_change_24h = Column(Float)

    token = relationship("Token", back_populates="prices")

    def __repr__(self):
        return f"<PriceData(token_id={self.token_id}, price={self.price}, timestamp='{self.timestamp}')>"

class HolderStats(Base):
    __tablename__ = 'holder_stats'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_holders = Column(Integer)
    active_holders_24h = Column(Integer)
    concentration_score = Column(Float)
    avg_balance = Column(Float)
    top_10_percent_share = Column(Float)

    token = relationship("Token", back_populates="holder_stats")

    def __repr__(self):
        return f"<HolderStats(token_id={self.token_id}, total_holders={self.total_holders}, timestamp='{self.timestamp}')>"

class MomentumScore(Base):
    __tablename__ = 'momentum_scores'

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_score = Column(Float, nullable=False)
    price_score = Column(Float)
    volume_score = Column(Float)
    holder_score = Column(Float)
    liquidity_score = Column(Float)
    signal_strength = Column(Float)

    token = relationship("Token", back_populates="momentum_scores")

    def __repr__(self):
        return f"<MomentumScore(token_id={self.token_id}, total_score={self.total_score}, timestamp='{self.timestamp}')>"