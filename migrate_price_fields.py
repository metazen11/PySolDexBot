#!/usr/bin/env python3
"""
Add missing price fields using the bidirectional field system
"""

import sqlite3
from ui_field_config import UIFieldManager

def migrate_price_fields():
    """Add missing price fields to database"""

    # Missing price fields that the UI expects
    missing_fields = [
        {
            'id': 'price_usd',
            'header': 'Price USD',
            'db_field': 'price_usd',
            'sortable': True,
            'type': 'currency',
            'display_format': 'price',
            'width': '100px'
        },
        {
            'id': 'price_change_5m',
            'header': '5m Change',
            'db_field': 'price_change_5m',
            'sortable': True,
            'type': 'percentage',
            'display_format': 'price_change',
            'width': '80px'
        },
        {
            'id': 'price_change_24h',
            'header': '24h Change',
            'db_field': 'price_change_24h',
            'sortable': True,
            'type': 'percentage',
            'display_format': 'price_change',
            'width': '80px'
        },
        {
            'id': 'last_price_update',
            'header': 'Last Update',
            'db_field': 'last_price_update',
            'sortable': True,
            'type': 'text',
            'display_format': 'timestamp',
            'width': '120px'
        }
    ]

    # Use the bidirectional field manager
    manager = UIFieldManager()

    print("🔄 Adding missing price fields to database...")

    for field in missing_fields:
        try:
            manager._add_db_field(field)
        except Exception as e:
            print(f"⚠️  Error adding {field['db_field']}: {e}")

    # Verify fields were added
    conn = sqlite3.connect('raydium_pools.db')
    cursor = conn.execute("PRAGMA table_info(pools)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    print("\n📊 Current price-related columns:")
    price_columns = [col for col in columns if 'price' in col.lower() or 'change' in col.lower()]
    for col in price_columns:
        print(f"  ✅ {col}")

    print(f"\n🎉 Total columns in pools table: {len(columns)}")

if __name__ == "__main__":
    migrate_price_fields()