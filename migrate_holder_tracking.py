#!/usr/bin/env python3
"""
Holder Tracking Migration: Add holder analytics to price_history
Extends existing time-series infrastructure for holder growth tracking
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_holder_tracking():
    """Add holder tracking fields to price_history table"""
    conn = sqlite3.connect('raydium_pools.db')
    cursor = conn.cursor()

    try:
        # Check existing columns in price_history
        cursor.execute("PRAGMA table_info(price_history)")
        columns = [column[1] for column in cursor.fetchall()]

        # Holder tracking columns to add
        holder_columns = [
            ('holder_count', 'INTEGER'),
            ('unique_traders_5m', 'INTEGER'),
            ('unique_traders_1h', 'INTEGER'),
            ('new_holders_5m', 'INTEGER'),  # New holders in last 5 minutes
            ('holder_concentration_top10', 'REAL'),  # % held by top 10 holders
        ]

        missing_columns = [(col, type_def) for col, type_def in holder_columns if col not in columns]

        if not missing_columns:
            logger.info("✅ All holder tracking columns already exist")
            return

        logger.info(f"🔧 Adding holder tracking columns: {[col for col, _ in missing_columns]}")

        # Add missing columns
        for col_name, col_type in missing_columns:
            try:
                cursor.execute(f'ALTER TABLE price_history ADD COLUMN {col_name} {col_type}')
                logger.info(f"✅ Added {col_name} column")
            except Exception as e:
                logger.warning(f"Column {col_name} may already exist: {e}")

        # Create indexes for holder analytics
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_holder_count ON price_history(holder_count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_holder_growth ON price_history(token_address, timestamp)')
            logger.info("✅ Created holder tracking indexes")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

        # Add computed columns to pools table for quick access
        pools_columns = [
            ('current_holder_count', 'INTEGER'),
            ('holder_growth_24h', 'REAL'),  # Percentage change in 24h
            ('holder_trend', 'TEXT'),  # 'growing', 'stable', 'declining'
            ('avg_holder_growth_7d', 'REAL'),  # Average daily growth over 7 days
        ]

        cursor.execute("PRAGMA table_info(pools)")
        existing_pools_columns = [column[1] for column in cursor.fetchall()]

        missing_pools_columns = [(col, type_def) for col, type_def in pools_columns
                                if col not in existing_pools_columns]

        for col_name, col_type in missing_pools_columns:
            try:
                cursor.execute(f'ALTER TABLE pools ADD COLUMN {col_name} {col_type}')
                logger.info(f"✅ Added {col_name} to pools table")
            except Exception as e:
                logger.warning(f"Column {col_name} may already exist: {e}")

        conn.commit()
        logger.info("🎉 Holder tracking migration completed!")

        # Show current schema
        cursor.execute("PRAGMA table_info(price_history)")
        price_history_cols = [col[1] for col in cursor.fetchall()]
        logger.info(f"📊 Price history columns: {len(price_history_cols)} total")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_holder_tracking()