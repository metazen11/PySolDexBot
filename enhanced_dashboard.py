#!/usr/bin/env python3
"""
Enhanced Dashboard with Advanced Security Filtering
Optimized for speed and better token analysis
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import aiohttp
from config import SecurityFilters, PerformanceConfig, DASHBOARD_PORT

app = Flask(__name__)

class EnhancedDashboard:
    def __init__(self):
        self.database_file = 'raydium_pools.db'

    def get_db_connection(self):
        conn = sqlite3.connect(self.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn

    def get_advanced_stats(self):
        """Get comprehensive statistics"""
        conn = self.get_db_connection()

        # Basic stats
        total_pools = conn.execute('SELECT COUNT(*) FROM pools').fetchone()[0]

        # Recent discoveries
        one_day_ago = datetime.now() - timedelta(days=1)
        recent_pools = conn.execute(
            'SELECT COUNT(*) FROM pools WHERE discovered_at > ?', (one_day_ago,)
        ).fetchone()[0]

        # Safe tokens count
        safe_tokens = conn.execute(
            'SELECT COUNT(*) FROM pools WHERE is_safe = 1 AND discovered_at > ?',
            (one_day_ago,)
        ).fetchone()[0]

        # High-value discoveries
        high_value = conn.execute(
            'SELECT COUNT(*) FROM pools WHERE liquidity > ? AND discovered_at > ?',
            (SecurityFilters.MIN_LIQUIDITY_PREMIUM, one_day_ago)
        ).fetchone()[0]

        # Average safety score
        avg_safety = conn.execute(
            'SELECT AVG(safety_score) FROM pools WHERE discovered_at > ? AND safety_score > 0',
            (one_day_ago,)
        ).fetchone()[0] or 0

        conn.close()

        return {
            'total_pools': total_pools,
            'recent_pools_24h': recent_pools,
            'safe_tokens_24h': safe_tokens,
            'high_value_tokens': high_value,
            'avg_safety_score': round(avg_safety, 1),
            'last_updated': datetime.now().isoformat()
        }

    def get_premium_tokens(self):
        """Get premium tier tokens with highest safety scores"""
        conn = self.get_db_connection()

        six_hours_ago = datetime.now() - timedelta(hours=6)
        tokens = conn.execute('''
            SELECT name, token_address, liquidity, volume24h, discovered_at,
                   is_pump_token, safety_score, holder_count, top_holder_percent,
                   mint_authority_renounced, freeze_authority_renounced,
                   is_active, activity_score, momentum_indicator, volume_last_hour, trades_last_hour
            FROM pools
            WHERE discovered_at > ?
            AND is_safe = 1
            AND safety_score >= 8
            AND liquidity > ?
            AND volume24h > ?
            ORDER BY activity_score DESC, safety_score DESC, liquidity DESC
            LIMIT 10
        ''', (six_hours_ago, SecurityFilters.MIN_LIQUIDITY_PREMIUM, SecurityFilters.MIN_VOLUME_PREMIUM)).fetchall()

        token_list = []
        for token in tokens:
            token_list.append({
                'name': token['name'],
                'token_address': token['token_address'],
                'liquidity': token['liquidity'],
                'volume24h': token['volume24h'],
                'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
                'safety_score': token['safety_score'],
                'holder_count': token['holder_count'],
                'top_holder_percent': token['top_holder_percent'],
                'mint_authority_renounced': bool(token['mint_authority_renounced']),
                'freeze_authority_renounced': bool(token['freeze_authority_renounced']),
                'is_pump_token': bool(token['is_pump_token']),
                'is_active': bool(token['is_active']) if token['is_active'] is not None else False,
                'activity_score': token['activity_score'] if token['activity_score'] is not None else 0,
                'momentum_indicator': token['momentum_indicator'] if token['momentum_indicator'] else 'unknown',
                'volume_last_hour': token['volume_last_hour'] if token['volume_last_hour'] is not None else 0,
                'trades_last_hour': token['trades_last_hour'] if token['trades_last_hour'] is not None else 0,
                'solscan_url': f"https://solscan.io/token/{token['token_address']}",
                'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}",
                'raydium_url': f"https://raydium.io/swap?inputCurrency=sol&outputCurrency={token['token_address']}"
            })

        conn.close()
        return token_list

    def get_recent_discoveries(self):
        """Get recent token discoveries with basic filtering"""
        conn = self.get_db_connection()

        two_hours_ago = datetime.now() - timedelta(hours=SecurityFilters.DISCOVERY_WINDOW_HOURS)
        tokens = conn.execute('''
            SELECT name, token_address, liquidity, volume24h, discovered_at,
                   is_pump_token, safety_score
            FROM pools
            WHERE discovered_at > ?
            AND liquidity > ?
            ORDER BY discovered_at DESC
            LIMIT 25
        ''', (two_hours_ago, SecurityFilters.MIN_LIQUIDITY_DISCOVERY)).fetchall()

        token_list = []
        for token in tokens:
            # Calculate risk level
            risk_level = "high"
            if token['safety_score'] >= 7:
                risk_level = "low"
            elif token['safety_score'] >= 4:
                risk_level = "medium"

            token_list.append({
                'name': token['name'],
                'token_address': token['token_address'],
                'liquidity': token['liquidity'],
                'volume24h': token['volume24h'],
                'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
                'safety_score': token['safety_score'],
                'risk_level': risk_level,
                'is_pump_token': bool(token['is_pump_token']),
                'solscan_url': f"https://solscan.io/token/{token['token_address']}",
                'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}"
            })

        conn.close()
        return token_list

    def get_safe_tokens(self):
        """Get verified safe tokens"""
        conn = self.get_db_connection()

        six_hours_ago = datetime.now() - timedelta(hours=SecurityFilters.SAFE_WINDOW_HOURS)
        tokens = conn.execute('''
            SELECT name, token_address, liquidity, volume24h, discovered_at,
                   is_pump_token, safety_score, holder_count, top_holder_percent
            FROM pools
            WHERE discovered_at > ?
            AND is_safe = 1
            AND safety_score >= 6
            ORDER BY safety_score DESC, liquidity DESC
            LIMIT 20
        ''', (six_hours_ago,)).fetchall()

        safe_tokens = []
        for token in tokens:
            safe_tokens.append({
                'name': token['name'],
                'token_address': token['token_address'],
                'liquidity': token['liquidity'],
                'volume24h': token['volume24h'],
                'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
                'safety_score': token['safety_score'],
                'holder_count': token['holder_count'],
                'holder_concentration': f"{token['top_holder_percent']*100:.1f}%" if token['top_holder_percent'] else "N/A",
                'solscan_url': f"https://solscan.io/token/{token['token_address']}",
                'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}"
            })

        conn.close()
        return safe_tokens

# Flask app setup
dashboard = EnhancedDashboard()

@app.route('/')
def enhanced_dashboard():
    return render_template('enhanced_dashboard.html')

@app.route('/api/stats')
def get_stats():
    return jsonify(dashboard.get_advanced_stats())

@app.route('/api/recent-tokens')
def get_recent_tokens():
    return jsonify(dashboard.get_recent_discoveries())

@app.route('/api/safe-tokens')
def get_safe_tokens():
    return jsonify(dashboard.get_safe_tokens())

@app.route('/api/premium-tokens')
def get_premium_tokens():
    return jsonify(dashboard.get_premium_tokens())

@app.route('/api/hot-tokens')
def get_hot_tokens():
    """Get tokens with high recent trading activity"""
    conn = dashboard.get_db_connection()

    thirty_minutes_ago = datetime.now() - timedelta(minutes=30)
    tokens = conn.execute('''
        SELECT name, token_address, liquidity, volume24h, discovered_at,
               is_pump_token, safety_score, is_active, activity_score,
               momentum_indicator, volume_last_hour, trades_last_hour
        FROM pools
        WHERE discovered_at > ?
        AND is_active = 1
        AND activity_score >= 5
        AND liquidity > 5000
        ORDER BY activity_score DESC, volume_last_hour DESC
        LIMIT 15
    ''', (thirty_minutes_ago,)).fetchall()

    hot_tokens = []
    for token in tokens:
        # Get momentum emoji
        momentum = token['momentum_indicator'] or 'unknown'
        momentum_emoji = {
            'hot': '🔥',
            'active': '⚡',
            'moderate': '📈',
            'low': '📉',
            'unknown': '❓'
        }.get(momentum, '❓')

        hot_tokens.append({
            'name': token['name'],
            'token_address': token['token_address'],
            'liquidity': token['liquidity'],
            'volume24h': token['volume24h'],
            'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
            'safety_score': token['safety_score'] if token['safety_score'] else 0,
            'activity_score': token['activity_score'] if token['activity_score'] else 0,
            'momentum_indicator': momentum,
            'momentum_emoji': momentum_emoji,
            'volume_last_hour': token['volume_last_hour'] if token['volume_last_hour'] else 0,
            'trades_last_hour': token['trades_last_hour'] if token['trades_last_hour'] else 0,
            'is_pump_token': bool(token['is_pump_token']),
            'solscan_url': f"https://solscan.io/token/{token['token_address']}",
            'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}"
        })

    conn.close()
    return jsonify(hot_tokens)

if __name__ == '__main__':
    # Disable template caching
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(debug=True, host='0.0.0.0', port=8082)