#!/usr/bin/env python3
"""
Database Migration: Add Honeypot Detection Fields
Adds honeypot detection columns to existing pools table
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add honeypot detection fields to existing database"""
    conn = sqlite3.connect('raydium_pools.db')
    cursor = conn.cursor()

    try:
        # Check if honeypot columns already exist
        cursor.execute("PRAGMA table_info(pools)")
        columns = [column[1] for column in cursor.fetchall()]

        honeypot_columns = ['is_honeypot', 'honeypot_score', 'sell_ratio', 'honeypot_checked_at']
        missing_columns = [col for col in honeypot_columns if col not in columns]

        if not missing_columns:
            logger.info("✅ Honeypot detection fields already exist")
            return

        logger.info(f"🔧 Adding missing honeypot columns: {missing_columns}")

        # Add missing columns
        if 'is_honeypot' in missing_columns:
            cursor.execute('ALTER TABLE pools ADD COLUMN is_honeypot INTEGER DEFAULT 0')
            logger.info("✅ Added is_honeypot column")

        if 'honeypot_score' in missing_columns:
            cursor.execute('ALTER TABLE pools ADD COLUMN honeypot_score INTEGER DEFAULT 0')
            logger.info("✅ Added honeypot_score column")

        if 'sell_ratio' in missing_columns:
            cursor.execute('ALTER TABLE pools ADD COLUMN sell_ratio REAL DEFAULT 0')
            logger.info("✅ Added sell_ratio column")

        if 'honeypot_checked_at' in missing_columns:
            cursor.execute('ALTER TABLE pools ADD COLUMN honeypot_checked_at TIMESTAMP')
            logger.info("✅ Added honeypot_checked_at column")

        # Create indexes for honeypot fields
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_honeypot ON pools(is_honeypot)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_honeypot_score ON pools(honeypot_score)')
            logger.info("✅ Created honeypot indexes")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

        conn.commit()
        logger.info("🎉 Database migration completed successfully!")

        # Get some stats
        cursor.execute("SELECT COUNT(*) FROM pools")
        total_tokens = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pools WHERE is_honeypot = 1")
        honeypot_tokens = cursor.fetchone()[0]

        logger.info(f"📊 Database stats: {total_tokens} total tokens, {honeypot_tokens} flagged as honeypots")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()