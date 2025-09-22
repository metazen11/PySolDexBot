#!/usr/bin/env python3
"""
Database Migration: Add Scanner Columns
Adds columns expected by the optimized scanner
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add scanner columns to existing database"""
    conn = sqlite3.connect('raydium_pools.db')
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(pools)")
        columns = [column[1] for column in cursor.fetchall()]

        # Expected scanner columns
        scanner_columns = [
            ('is_safe', 'INTEGER DEFAULT 0'),
            ('safety_score', 'INTEGER DEFAULT 0'),
            ('holder_count', 'INTEGER'),
            ('top_holder_percent', 'REAL'),
            ('mint_authority_renounced', 'INTEGER DEFAULT 0'),
            ('freeze_authority_renounced', 'INTEGER DEFAULT 0'),
            ('base_mint', 'TEXT'),
            ('quote_mint', 'TEXT'),
            ('created_at', 'TIMESTAMP')
        ]

        missing_columns = [(col, type_def) for col, type_def in scanner_columns if col not in columns]

        if not missing_columns:
            logger.info("✅ All scanner columns already exist")
            return

        logger.info(f"🔧 Adding missing scanner columns: {[col for col, _ in missing_columns]}")

        # Add missing columns
        for col_name, col_type in missing_columns:
            try:
                cursor.execute(f'ALTER TABLE pools ADD COLUMN {col_name} {col_type}')
                logger.info(f"✅ Added {col_name} column")
            except Exception as e:
                logger.warning(f"Column {col_name} may already exist: {e}")

        # Create indexes that the scanner expects
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_safe ON pools(is_safe)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_safety_score ON pools(safety_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_composite_safe ON pools(is_safe, liquidity, volume24h)')
            logger.info("✅ Created scanner indexes")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

        conn.commit()
        logger.info("🎉 Scanner database migration completed!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()