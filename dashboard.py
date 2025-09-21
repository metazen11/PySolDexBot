#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

DATABASE_FILE = 'raydium_pools.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    conn = get_db_connection()

    # Get basic stats
    total_pools = conn.execute('SELECT COUNT(*) FROM pools').fetchone()[0]

    # Get recent discoveries (last 24 hours)
    one_day_ago = datetime.now() - timedelta(days=1)
    recent_pools = conn.execute(
        'SELECT COUNT(*) FROM pools WHERE discovered_at > ?',
        (one_day_ago,)
    ).fetchone()[0]

    # Get safe tokens (no mint/freeze authority)
    # This would need additional columns in the database

    conn.close()

    return jsonify({
        'total_pools': total_pools,
        'recent_pools_24h': recent_pools,
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/recent-tokens')
def get_recent_tokens():
    conn = get_db_connection()

    # Get recent tokens discovered in last 2 hours with reasonable liquidity
    two_hours_ago = datetime.now() - timedelta(hours=2)
    tokens = conn.execute('''
        SELECT name, token_address, liquidity, volume24h, discovered_at, is_pump_token
        FROM pools
        WHERE discovered_at > ? AND liquidity > 500
        ORDER BY discovered_at DESC
        LIMIT 20
    ''', (two_hours_ago,)).fetchall()

    token_list = []
    for token in tokens:
        token_list.append({
            'name': token['name'],
            'token_address': token['token_address'],
            'liquidity': token['liquidity'],
            'volume24h': token['volume24h'],
            'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
            'is_pump_token': bool(token['is_pump_token']),
            'solscan_url': f"https://solscan.io/token/{token['token_address']}",
            'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}"
        })

    conn.close()

    return jsonify(token_list)

@app.route('/api/safe-tokens')
def get_safe_tokens():
    """Get tokens that pass basic safety checks"""
    conn = get_db_connection()

    # Get recent tokens with decent liquidity and volume from last 6 hours
    six_hours_ago = datetime.now() - timedelta(hours=6)
    tokens = conn.execute('''
        SELECT name, token_address, liquidity, volume24h, discovered_at, is_pump_token
        FROM pools
        WHERE discovered_at > ?
        AND liquidity > 10000
        AND volume24h > 500
        ORDER BY discovered_at DESC, liquidity DESC
        LIMIT 15
    ''', (six_hours_ago,)).fetchall()

    safe_tokens = []
    for token in tokens:
        safe_tokens.append({
            'name': token['name'],
            'token_address': token['token_address'],
            'liquidity': token['liquidity'],
            'volume24h': token['volume24h'],
            'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
            'safety_score': 7,  # Placeholder - would calculate based on multiple factors
            'solscan_url': f"https://solscan.io/token/{token['token_address']}",
            'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}"
        })

    conn.close()

    return jsonify(safe_tokens)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    # Disable template caching
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(debug=True, host='0.0.0.0', port=8080)