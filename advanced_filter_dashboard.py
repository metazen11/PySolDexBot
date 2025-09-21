#!/usr/bin/env python3
"""
Advanced Filtering Dashboard - Competitive advantage over DexTools/DexScreener
Real-time token filtering with superior data processing
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from config import SecurityFilters

app = Flask(__name__)

class AdvancedFilterSystem:
    def __init__(self):
        self.database_file = 'raydium_pools.db'

    def get_db_connection(self):
        conn = sqlite3.connect(self.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn

    def apply_filters(self, filters):
        """Apply advanced filtering with competitive advantages"""
        conn = self.get_db_connection()

        # Base query with only existing columns (simplified for compatibility)
        base_query = '''
            SELECT name, token_address, liquidity, volume24h, discovered_at, is_pump_token
            FROM pools
            WHERE 1=1
        '''

        conditions = []
        params = []

        # Time-based filters
        if filters.get('time_range'):
            time_map = {
                '1h': timedelta(hours=1),
                '6h': timedelta(hours=6),
                '24h': timedelta(hours=24),
                '7d': timedelta(days=7)
            }
            if filters['time_range'] in time_map:
                cutoff = datetime.now() - time_map[filters['time_range']]
                conditions.append('discovered_at > ?')
                params.append(cutoff)

        # Liquidity filters
        if filters.get('min_liquidity'):
            conditions.append('liquidity >= ?')
            params.append(filters['min_liquidity'])

        if filters.get('max_liquidity'):
            conditions.append('liquidity <= ?')
            params.append(filters['max_liquidity'])

        # Volume filters
        if filters.get('min_volume_24h'):
            conditions.append('volume24h >= ?')
            params.append(filters['min_volume_24h'])

        # Always exclude completely dead tokens (zero volume)
        conditions.append('volume24h > 0')  # Remove absolute zero volume tokens

        # Volume 1h filter (PLACEHOLDER - will work after schema enhancement)
        # For now, skip this filter as the column doesn't exist yet

        # Activity filters (SIMPLIFIED - will be available after schema enhancement)
        if filters.get('activity_level'):
            # For now, use volume as a proxy for activity
            activity_volume_map = {
                'hot': 10000,    # High volume = hot
                'active': 5000,  # Medium volume = active
                'moderate': 1000, # Low volume = moderate
                'any': 0         # Any volume
            }
            if filters['activity_level'] in activity_volume_map:
                conditions.append('volume24h >= ?')
                params.append(activity_volume_map[filters['activity_level']])

        # Safety filters (SIMPLIFIED - based on liquidity for now)
        if filters.get('safety_level'):
            safety_liquidity_map = {
                'premium': 50000,  # High liquidity = safer
                'safe': 20000,     # Medium liquidity
                'moderate': 10000, # Basic liquidity
                'any': 0           # Any liquidity
            }
            if filters['safety_level'] in safety_liquidity_map:
                conditions.append('liquidity >= ?')
                params.append(safety_liquidity_map[filters['safety_level']])

        # Risk score filters (will be applied post-query since risk score is calculated)
        max_risk_score = filters.get('max_risk_score', 10)  # Default allow all risk levels

        # Platform filters
        if filters.get('platform'):
            if filters['platform'] == 'pump_only':
                conditions.append('is_pump_token = 1')
            elif filters['platform'] == 'no_pump':
                conditions.append('is_pump_token = 0')

        # Advanced filters (PLACEHOLDER - will work after schema enhancement)
        # For now, these filters are noted but not implemented until schema is enhanced
        # - Authority filters (mint/freeze renouncement)
        # - Holder concentration filters
        # - Recent trading activity
        # - Price momentum filters

        # Build final query
        if conditions:
            base_query += ' AND ' + ' AND '.join(conditions)

        # Sorting
        sort_map = {
            'newest': 'discovered_at DESC',
            'liquidity': 'liquidity DESC',
            'volume': 'volume24h DESC',
            'marketcap': 'liquidity DESC',  # Use liquidity as proxy for market cap
            'activity': 'liquidity DESC',   # Simplified to liquidity until enhanced
            'safety': 'liquidity DESC',     # Simplified to liquidity until enhanced
            'momentum': 'volume24h DESC'    # Use volume as momentum proxy
        }

        sort_by = filters.get('sort_by', 'newest')
        if sort_by in sort_map:
            base_query += f' ORDER BY {sort_map[sort_by]}'

        # Limit results
        limit = min(filters.get('limit', 50), 200)  # Cap at 200
        base_query += f' LIMIT {limit}'

        # Execute query
        results = conn.execute(base_query, params).fetchall()
        conn.close()

        # Format results (simplified for current schema)
        tokens = []
        for token in results:
            # Calculate simplified metrics based on available data
            risk_score = self.calculate_simplified_risk_score(token)
            opportunity_score = self.calculate_simplified_opportunity_score(token)

            # Calculate approximate market cap (liquidity * 1.5 as improved estimate)
            market_cap = (token['liquidity'] * 1.5) if token['liquidity'] else 0

            tokens.append({
                'name': token['name'],
                'token_address': token['token_address'],
                'liquidity': token['liquidity'],
                'volume24h': token['volume24h'],
                'market_cap': market_cap,  # Market cap (estimated)
                'volume_1h': 0,  # Placeholder until schema enhanced
                'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
                'safety_score': 0,  # Placeholder
                'activity_score': min(int(token['volume24h'] / 1000), 10) if token['volume24h'] else 0,  # Volume-based proxy
                'momentum': 'unknown',  # Placeholder
                'price_change_1h': 0,  # Placeholder
                'trades_1h': 0,  # Placeholder
                'holder_concentration': 0,  # Placeholder
                'is_pump_token': bool(token['is_pump_token']),
                'mint_renounced': False,  # Placeholder
                'freeze_renounced': False,  # Placeholder
                'is_active': True,  # Assume active if discovered recently
                # COMPETITIVE ADVANTAGE METRICS (simplified)
                'risk_score': risk_score,
                'opportunity_score': opportunity_score,
                'composite_score': (opportunity_score - risk_score),
                'solscan_url': f"https://solscan.io/token/{token['token_address']}",
                'dexscreener_url': f"https://dexscreener.com/solana/{token['token_address']}"
            })

        # Apply risk score filtering if specified
        max_risk_score = filters.get('max_risk_score', 10)
        if max_risk_score < 10:
            tokens = [token for token in tokens if token['risk_score'] <= max_risk_score]

        return tokens

    def calculate_simplified_risk_score(self, token):
        """Calculate simplified risk score based on available data"""
        risk = 0

        # Platform risk (pump tokens are actually safer)
        if not token['is_pump_token']:
            risk += 2

        # Low liquidity = higher risk (possible rug pull setup)
        if token['liquidity'] and token['liquidity'] < 5000:
            risk += 4  # Very high risk
        elif token['liquidity'] and token['liquidity'] < 10000:
            risk += 3  # High risk
        elif token['liquidity'] and token['liquidity'] < 50000:
            risk += 1  # Moderate risk

        # Volume vs Liquidity ratio analysis (honeypot indicator)
        if token['liquidity'] and token['volume24h']:
            volume_liquidity_ratio = token['volume24h'] / token['liquidity']
            if volume_liquidity_ratio > 10:  # Extremely high volume relative to liquidity
                risk += 2  # Possible pump and dump
            elif volume_liquidity_ratio < 0.01:  # Very low volume relative to liquidity
                risk += 1  # Possible honeypot

        # Market cap analysis (market cap = liquidity * 1.5 from our calculation)
        market_cap = (token['liquidity'] * 1.5) if token['liquidity'] else 0
        if market_cap < 10000:  # Very low market cap tokens are riskier
            risk += 2

        return min(risk, 10)

    def calculate_simplified_opportunity_score(self, token):
        """Calculate simplified opportunity score based on available data"""
        opportunity = 0

        # Volume opportunity
        volume24h = token['volume24h'] or 0
        if volume24h > 50000:
            opportunity += 4
        elif volume24h > 10000:
            opportunity += 3
        elif volume24h > 5000:
            opportunity += 2
        elif volume24h > 1000:
            opportunity += 1

        # Liquidity opportunity
        liquidity = token['liquidity'] or 0
        if liquidity > 100000:
            opportunity += 2
        elif liquidity > 50000:
            opportunity += 1

        # Pump token bonus (safer platform)
        if token['is_pump_token']:
            opportunity += 1

        return min(opportunity, 10)

    def calculate_risk_score(self, token):
        """Calculate risk score (0-10, lower is better)"""
        risk = 0

        # Authority risks
        if not token['mint_authority_renounced']:
            risk += 3
        if not token['freeze_authority_renounced']:
            risk += 3

        # Concentration risk
        if token['top_holder_percent'] and token['top_holder_percent'] > 0.5:
            risk += 2
        elif token['top_holder_percent'] and token['top_holder_percent'] > 0.3:
            risk += 1

        # Activity risk (no activity = higher risk)
        if not token['is_active']:
            risk += 1

        # Platform risk (pump tokens actually safer)
        if not token['is_pump_token']:
            risk += 1

        return min(risk, 10)

    def calculate_opportunity_score(self, token):
        """Calculate opportunity score (0-10, higher is better)"""
        opportunity = 0

        # Activity opportunity
        activity_score = token['activity_score'] or 0
        opportunity += min(activity_score, 4)

        # Volume opportunity
        volume_1h = token['volume_last_hour'] or 0
        if volume_1h > 10000:
            opportunity += 3
        elif volume_1h > 5000:
            opportunity += 2
        elif volume_1h > 1000:
            opportunity += 1

        # Price momentum opportunity
        price_change = token['price_change_1h'] or 0
        if 5 <= price_change <= 25:  # Sweet spot
            opportunity += 2
        elif price_change > 0:
            opportunity += 1

        # Safety opportunity
        safety_score = token['safety_score'] or 0
        if safety_score >= 8:
            opportunity += 1

        return min(opportunity, 10)

    def get_filter_presets(self):
        """Get predefined filter presets for quick access"""
        return {
            'moonshot_hunters': {
                'name': '🚀 Moonshot Hunters',
                'description': 'High potential, moderate risk tokens',
                'filters': {
                    'time_range': '6h',
                    'min_liquidity': 5000,
                    'activity_level': 'active',
                    'safety_level': 'moderate',
                    'platform': 'pump_only',
                    'sort_by': 'activity'
                }
            },
            'safe_gainers': {
                'name': '✅ Safe Gainers',
                'description': 'High safety, proven tokens',
                'filters': {
                    'time_range': '24h',
                    'min_liquidity': 20000,
                    'safety_level': 'premium',
                    'mint_renounced': True,
                    'freeze_renounced': True,
                    'max_holder_concentration': 30,
                    'sort_by': 'safety'
                }
            },
            'hot_momentum': {
                'name': '🔥 Hot Momentum',
                'description': 'Actively trading with momentum',
                'filters': {
                    'time_range': '1h',
                    'min_volume_1h': 1000,
                    'activity_level': 'hot',
                    'recent_trades_only': True,
                    'price_trend': 'pumping',
                    'sort_by': 'momentum'
                }
            },
            'dip_opportunities': {
                'name': '📉 Dip Opportunities',
                'description': 'Quality tokens on discount',
                'filters': {
                    'time_range': '6h',
                    'min_liquidity': 10000,
                    'safety_level': 'safe',
                    'price_trend': 'dipping',
                    'activity_level': 'moderate',
                    'sort_by': 'liquidity'
                }
            },
            'whale_safe': {
                'name': '🐋 Whale-Safe',
                'description': 'Distributed ownership, low concentration',
                'filters': {
                    'time_range': '24h',
                    'min_liquidity': 50000,
                    'max_holder_concentration': 20,
                    'mint_renounced': True,
                    'freeze_renounced': True,
                    'sort_by': 'liquidity'
                }
            }
        }

# Initialize filter system
filter_system = AdvancedFilterSystem()

@app.route('/')
def filter_dashboard():
    return render_template('filter_dashboard.html')

@app.route('/api/recent')
def get_recent_tokens():
    """Get recent tokens with volume and security filters for initial display"""
    filters = {
        'min_volume_24h': 100,  # Only show tokens with at least $100 volume
        'max_risk_score': 6,    # Filter out very high risk tokens (>6 out of 10)
        'sort_by': 'volume',    # Sort by volume to show most active first
        'limit': 100            # Get more tokens to filter through
    }
    all_results = filter_system.apply_filters(filters)

    # Additional security filtering based on risk scores
    safe_results = [token for token in all_results if token['risk_score'] <= 6]

    # Limit to 50 safest tokens
    safe_results = safe_results[:50]

    return jsonify({
        'tokens': safe_results,
        'count': len(safe_results),
        'filters_applied': filters,
        'security_filtered': len(all_results) - len(safe_results)
    })

@app.route('/api/filter', methods=['POST'])
def apply_filters():
    """Apply filters and return results"""
    filters = request.json or {}
    results = filter_system.apply_filters(filters)
    return jsonify({
        'tokens': results,
        'count': len(results),
        'filters_applied': filters
    })

@app.route('/api/presets')
def get_presets():
    """Get filter presets"""
    return jsonify(filter_system.get_filter_presets())

@app.route('/api/stats')
def get_filter_stats():
    """Get statistics for filtering UI"""
    conn = filter_system.get_db_connection()

    # Get ranges for slider inputs
    liquidity_range = conn.execute('SELECT MIN(liquidity), MAX(liquidity) FROM pools WHERE liquidity > 0').fetchone()
    volume_range = conn.execute('SELECT MIN(volume24h), MAX(volume24h) FROM pools WHERE volume24h > 0').fetchone()

    stats = {
        'liquidity_range': [liquidity_range[0] or 0, liquidity_range[1] or 0],
        'volume_range': [volume_range[0] or 0, volume_range[1] or 0],
        'total_tokens': conn.execute('SELECT COUNT(*) FROM pools').fetchone()[0],
        'active_tokens': conn.execute('SELECT COUNT(*) FROM pools WHERE is_active = 1').fetchone()[0],
        'pump_tokens': conn.execute('SELECT COUNT(*) FROM pools WHERE is_pump_token = 1').fetchone()[0]
    }

    conn.close()
    return jsonify(stats)

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(debug=True, host='0.0.0.0', port=8084)