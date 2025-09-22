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
import requests
import time

app = Flask(__name__)

# Known wrapped tokens and stablecoins to filter out
WRAPPED_TOKENS = {
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',   # USDT
    'So11111111111111111111111111111111111111112',    # SOL
    '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',   # RAY
}

# DexScreener API
DEXSCREENER_BASE = 'https://api.dexscreener.com/latest/dex/tokens'

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

        # Base query with honeypot detection fields, price data, and holder analytics
        base_query = '''
            SELECT p.name, p.token_address, p.liquidity, p.volume24h, p.discovered_at, p.is_pump_token,
                   COALESCE(p.is_honeypot, 0) as is_honeypot,
                   COALESCE(p.honeypot_score, 0) as honeypot_score,
                   COALESCE(p.sell_ratio, 0) as sell_ratio,
                   p.current_holder_count,
                   p.holder_growth_24h,
                   p.holder_trend,
                   p.avg_holder_growth_7d,
                   p.price_usd,
                   p.price_change_5m,
                   p.price_change_1h,
                   p.price_change_24h,
                   p.last_price_update,
                   p.liquidity as market_cap
            FROM pools p
            WHERE 1=1
        '''

        conditions = []
        params = []

        # Filter out wrapped tokens and stablecoins
        wrapped_placeholders = ','.join(['?' for _ in WRAPPED_TOKENS])
        conditions.append(f'p.token_address NOT IN ({wrapped_placeholders})')
        params.extend(WRAPPED_TOKENS)

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
                conditions.append('p.discovered_at > ?')
                params.append(cutoff)

        # Age-based filters for mature tokens
        if filters.get('min_age_hours'):
            min_age_cutoff = datetime.now() - timedelta(hours=filters['min_age_hours'])
            conditions.append('p.discovered_at <= ?')
            params.append(min_age_cutoff)

        if filters.get('max_age_days'):
            max_age_cutoff = datetime.now() - timedelta(days=filters['max_age_days'])
            conditions.append('p.discovered_at >= ?')
            params.append(max_age_cutoff)

        # Liquidity filters
        if filters.get('min_liquidity'):
            conditions.append('p.liquidity >= ?')
            params.append(filters['min_liquidity'])

        if filters.get('max_liquidity'):
            conditions.append('p.liquidity <= ?')
            params.append(filters['max_liquidity'])

        # Volume filters
        if filters.get('min_volume_24h'):
            conditions.append('p.volume24h >= ?')
            params.append(filters['min_volume_24h'])

        # Always exclude completely dead tokens (zero volume)
        conditions.append('p.volume24h > 0')  # Remove absolute zero volume tokens

        # Honeypot filtering
        if filters.get('exclude_honeypots', False):
            conditions.append('COALESCE(is_honeypot, 0) = 0')

        if filters.get('include_honeypots_only', False):
            conditions.append('COALESCE(is_honeypot, 0) = 1')

        if filters.get('max_honeypot_score') is not None:
            conditions.append('COALESCE(honeypot_score, 0) <= ?')
            params.append(filters['max_honeypot_score'])

        if filters.get('min_sell_ratio') is not None:
            conditions.append('COALESCE(sell_ratio, 0) >= ?')
            params.append(filters['min_sell_ratio'])

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
                conditions.append('p.volume24h >= ?')
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
                conditions.append('p.liquidity >= ?')
                params.append(safety_liquidity_map[filters['safety_level']])

        # Holder growth filters
        if filters.get('min_holder_count'):
            conditions.append('p.current_holder_count >= ?')
            params.append(filters['min_holder_count'])

        if filters.get('max_holder_count'):
            conditions.append('p.current_holder_count <= ?')
            params.append(filters['max_holder_count'])

        if filters.get('min_holder_growth_24h'):
            conditions.append('p.holder_growth_24h >= ?')
            params.append(filters['min_holder_growth_24h'])

        if filters.get('max_holder_growth_24h'):
            conditions.append('p.holder_growth_24h <= ?')
            params.append(filters['max_holder_growth_24h'])

        if filters.get('holder_trend'):
            if isinstance(filters['holder_trend'], list):
                trend_placeholders = ','.join(['?' for _ in filters['holder_trend']])
                conditions.append(f'p.holder_trend IN ({trend_placeholders})')
                params.extend(filters['holder_trend'])
            else:
                conditions.append('p.holder_trend = ?')
                params.append(filters['holder_trend'])

        # Risk score filters (will be applied post-query since risk score is calculated)
        max_risk_score = filters.get('max_risk_score', 10)  # Default allow all risk levels

        # Platform filters
        if filters.get('platform'):
            if filters['platform'] == 'pump_only':
                conditions.append('p.is_pump_token = 1')
            elif filters['platform'] == 'no_pump':
                conditions.append('p.is_pump_token = 0')

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

        # Format results with database honeypot data
        tokens = []
        for token in results:
            # Use database honeypot data (much faster than real-time calculation)
            db_honeypot_score = token['honeypot_score'] if token['honeypot_score'] is not None else 0
            db_is_honeypot = bool(token['is_honeypot']) if token['is_honeypot'] is not None else False
            db_sell_ratio = token['sell_ratio'] if token['sell_ratio'] is not None else 0

            # Skip confirmed honeypots if not explicitly requested
            if db_is_honeypot and not filters.get('include_honeypots_only', False):
                continue

            # Get latest price and momentum data
            price_data = self.get_latest_price_data(token['token_address'])
            momentum_score = self.calculate_momentum_score(token['token_address'])

            # Calculate simplified metrics based on available data
            risk_score = self.calculate_simplified_risk_score(token)
            opportunity_score = self.calculate_simplified_opportunity_score(token)

            # Add honeypot score to risk assessment
            risk_score += min(db_honeypot_score / 10, 3)  # Add up to 3 points for honeypot risk

            # Calculate market cap from price data or estimate
            if price_data and price_data.get('market_cap'):
                market_cap = price_data['market_cap']
            else:
                market_cap = (token['liquidity'] * 1.5) if token['liquidity'] else 0

            # Determine momentum category
            if momentum_score > 30:
                momentum_category = "bullish"
            elif momentum_score > 10:
                momentum_category = "positive"
            elif momentum_score > -10:
                momentum_category = "neutral"
            elif momentum_score > -30:
                momentum_category = "negative"
            else:
                momentum_category = "bearish"

            tokens.append({
                'name': token['name'],
                'token_address': token['token_address'],
                'liquidity': token['liquidity'],
                'volume24h': token['volume24h'],
                'market_cap': market_cap,
                'price_usd': price_data.get('price_usd') if price_data else None,
                'price_change_5m': price_data.get('price_change_5m') if price_data else 0,
                'price_change_1h': price_data.get('price_change_1h') if price_data else 0,
                'price_change_24h': price_data.get('price_change_24h') if price_data else 0,
                'volume_5m': price_data.get('volume_5m') if price_data else 0,
                'volume_1h': price_data.get('volume_1h') if price_data else 0,
                'trades_1h': (price_data.get('buys_5m', 0) + price_data.get('sells_5m', 0)) * 12 if price_data else 0,
                'discovered_at': token['discovered_at'].isoformat() if token['discovered_at'] else None,
                'safety_score': 0,  # Placeholder
                'activity_score': min(int(token['volume24h'] / 1000), 10) if token['volume24h'] else 0,
                'momentum_score': momentum_score,
                'momentum': momentum_category,
                'honeypot_score': db_honeypot_score,
                'sell_ratio': db_sell_ratio,
                'is_likely_honeypot': db_is_honeypot,
                'current_holder_count': token['current_holder_count'],
                'holder_growth_24h': token['holder_growth_24h'],
                'holder_trend': token['holder_trend'],
                'avg_holder_growth_7d': token['avg_holder_growth_7d'],
                'holder_concentration': 0,  # Placeholder
                'is_pump_token': bool(token['is_pump_token']),
                'mint_renounced': False,  # Placeholder
                'freeze_renounced': False,  # Placeholder
                'is_active': momentum_score > -50,  # Active if not heavily bearish
                'last_price_update': price_data.get('last_updated') if price_data else None,
                # COMPETITIVE ADVANTAGE METRICS
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

    def is_weekend_or_evening(self):
        """Check if it's weekend or evening (meme token prime time)"""
        from datetime import datetime
        now = datetime.now()
        # Weekend (Saturday=5, Sunday=6) or weekday evening (after 6PM)
        return now.weekday() >= 5 or now.hour >= 18 or now.hour <= 6

    def is_meme_token(self, token_name):
        """Simple heuristic to detect meme tokens vs utility tokens"""
        meme_indicators = [
            'pump', 'moon', 'doge', 'pepe', 'shib', 'elon', 'safe', 'inu',
            'baby', 'mini', 'floki', 'wojak', 'chad', 'cope', 'bonk',
            'goat', 'cat', 'frog', 'bear', 'bull', 'ape', 'monkey'
        ]
        name_lower = token_name.lower()
        return any(indicator in name_lower for indicator in meme_indicators)

    def get_latest_price_data(self, token_address):
        """Get latest price data from price_history table"""
        conn = self.get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT price_usd, price_change_5m, price_change_1h, price_change_24h,
                       volume_5m, volume_1h, buys_5m, sells_5m, market_cap, timestamp
                FROM price_history
                WHERE token_address = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (token_address,))

            result = cursor.fetchone()
            if result:
                return {
                    'price_usd': result[0],
                    'price_change_5m': result[1],
                    'price_change_1h': result[2],
                    'price_change_24h': result[3],
                    'volume_5m': result[4],
                    'volume_1h': result[5],
                    'buys_5m': result[6],
                    'sells_5m': result[7],
                    'market_cap': result[8],
                    'last_updated': result[9]
                }
            return None
        except Exception:
            # Table might not exist yet if price tracker hasn't run
            return None
        finally:
            conn.close()

    def calculate_momentum_score(self, token_address):
        """Calculate momentum score from price history"""
        conn = self.get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT price_usd, volume_5m, buys_5m, sells_5m, timestamp
                FROM price_history
                WHERE token_address = ?
                ORDER BY timestamp DESC
                LIMIT 6
            ''', (token_address,))

            history = cursor.fetchall()
            if len(history) < 2:
                return 0

            momentum_score = 0

            # Price momentum (50% of score)
            prices = [row[0] for row in history if row[0] is not None]
            if len(prices) >= 2:
                price_change = (prices[0] - prices[-1]) / prices[-1] if prices[-1] > 0 else 0
                momentum_score += min(price_change * 100, 50)

            # Volume momentum (25% of score)
            volumes = [row[1] for row in history if row[1] is not None]
            if len(volumes) >= 2:
                volume_trend = (volumes[0] - volumes[-1]) / volumes[-1] if volumes[-1] > 0 else 0
                momentum_score += min(volume_trend * 25, 25)

            # Buy pressure (25% of score)
            latest = history[0]
            if latest[2] is not None and latest[3] is not None:
                total_trades = latest[2] + latest[3]
                if total_trades > 0:
                    buy_ratio = latest[2] / total_trades
                    pressure_score = (buy_ratio - 0.5) * 50
                    momentum_score += pressure_score

            return max(-100, min(100, momentum_score))

        except Exception:
            return 0
        finally:
            conn.close()

    def detect_honeypot_indicators(self, token_address):
        """Advanced honeypot detection using buy/sell patterns"""
        conn = self.get_db_connection()
        honeypot_score = 0
        flags = []

        try:
            # Get recent trading data
            cursor = conn.execute('''
                SELECT buys_5m, sells_5m, volume_5m, price_change_5m, timestamp
                FROM price_history
                WHERE token_address = ?
                ORDER BY timestamp DESC
                LIMIT 12
            ''', (token_address,))

            recent_data = cursor.fetchall()
            if not recent_data:
                return honeypot_score, flags

            # Analyze sell activity patterns
            total_buys = sum(row[0] for row in recent_data if row[0] is not None)
            total_sells = sum(row[1] for row in recent_data if row[1] is not None)

            # RED FLAG 1: No sells despite buys (classic honeypot)
            if total_buys > 0 and total_sells == 0:
                honeypot_score += 50
                flags.append("🚨 HONEYPOT: Only buys, zero sells detected")

            # RED FLAG 2: Extremely low sell ratio
            elif total_buys > 0 and total_sells > 0:
                sell_ratio = total_sells / (total_buys + total_sells)
                if sell_ratio < 0.05:  # Less than 5% sells
                    honeypot_score += 40
                    flags.append(f"⚠️ HONEYPOT RISK: Very low sell activity ({sell_ratio:.1%})")
                elif sell_ratio < 0.15:  # Less than 15% sells
                    honeypot_score += 20
                    flags.append(f"⚠️ Suspicious: Low sell activity ({sell_ratio:.1%})")

            # RED FLAG 3: Price keeps rising with volume but no sells
            price_increases = 0
            for row in recent_data:
                if row[3] is not None and row[3] > 0:  # positive price change
                    price_increases += 1

            if price_increases >= len(recent_data) * 0.7 and total_sells == 0:
                honeypot_score += 30
                flags.append("🚨 HONEYPOT: Price rising with no sells")

            # RED FLAG 4: Consistent volume but no sell pressure
            recent_volumes = [row[2] for row in recent_data if row[2] is not None and row[2] > 0]
            if len(recent_volumes) >= 3 and total_sells == 0:
                honeypot_score += 25
                flags.append("⚠️ HONEYPOT RISK: Volume without sell pressure")

            return min(honeypot_score, 100), flags

        except Exception as e:
            return 0, []
        finally:
            conn.close()

    def is_likely_honeypot(self, token_address):
        """Simple boolean check if token is likely a honeypot"""
        honeypot_score, flags = self.detect_honeypot_indicators(token_address)
        return honeypot_score >= 40  # 40+ score = likely honeypot

    def get_filter_presets(self):
        """Get predefined filter presets with time-aware adjustments"""
        is_meme_time = self.is_weekend_or_evening()

        base_presets = {
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
                'description': f'Actively trading {"(meme time!)" if is_meme_time else "(utility focus)"}',
                'filters': {
                    'time_range': '7d',  # More realistic timeframe
                    'min_liquidity': 3000 if is_meme_time else 8000,
                    'activity_level': 'moderate',  # Reduced from 'active' (5000) to 'moderate' (1000)
                    'min_volume_24h': 1000 if is_meme_time else 3000,  # Reduced requirements
                    'sort_by': 'volume'
                }
            },
            'dip_opportunities': {
                'name': '📉 Dip Opportunities',
                'description': 'Quality tokens on discount',
                'filters': {
                    'time_range': '7d',  # More realistic timeframe
                    'min_liquidity': 5000,  # Reduced from 10000
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

        # Add proven longevity filters (always available)
        base_presets['exchange_worthy'] = {
            'name': '🏆 Exchange Worthy',
            'description': 'Mature tokens (6+ hours) with sustained activity',
            'filters': {
                'min_age_hours': 6,   # At least 6 hours old (proven initial stability)
                'max_age_days': 30,   # But not too old (still trending)
                'activity_level': 'moderate',  # Reduced from 'active' (5000) to 'moderate' (1000)
                'min_liquidity': 8000,      # Reduced from 15000
                'min_volume_24h': 3000,      # Reduced from 5000
                'safety_level': 'safe',      # Security standards
                'sort_by': 'volume'          # Sort by volume
            }
        }

        base_presets['anti_honeypot'] = {
            'name': '🍯🚫 Anti-Honeypot',
            'description': 'Tokens with proven sell activity (honeypot-safe)',
            'filters': {
                'min_volume_24h': 1000,     # Decent volume
                'activity_level': 'active',  # Recent activity
                'exclude_honeypots': True,   # Explicit honeypot filtering
                'min_sell_ratio': 0.15,     # At least 15% sells
                'sort_by': 'safety'
            }
        }

        base_presets['survivors'] = {
            'name': '💪 Survivors',
            'description': 'Tokens that have lasted and are still growing',
            'filters': {
                'min_age_hours': 4,      # At least 4 hours old (realistic for current data)
                'activity_level': 'active',  # Still active
                'min_liquidity': 10000,
                'min_volume_24h': 3000,
                'sort_by': 'volume'
            }
        }

        return base_presets

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

def get_dexscreener_data(token_address):
    """Get price change data from DexScreener"""
    try:
        url = f"{DEXSCREENER_BASE}/{token_address}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if 'pairs' in data and data['pairs']:
                best_pair = max(data['pairs'], key=lambda x: x.get('liquidity', {}).get('usd', 0))
                return {
                    'price_change_5m': best_pair.get('priceChange', {}).get('m5'),
                    'price_change_1h': best_pair.get('priceChange', {}).get('h1'),
                    'price_change_24h': best_pair.get('priceChange', {}).get('h24'),
                    'price_usd': best_pair.get('priceUsd'),
                    'buys_5m': best_pair.get('txns', {}).get('m5', {}).get('buys', 0),
                    'sells_5m': best_pair.get('txns', {}).get('m5', {}).get('sells', 0)
                }
        return None
    except Exception as e:
        print(f"Error fetching DexScreener data: {e}")
        return None

@app.route('/api/rugcheck/<token_address>')
def rugcheck_token(token_address):
    """Basic rug check analysis"""
    try:
        # Get DexScreener data for analysis
        dex_data = get_dexscreener_data(token_address)

        rug_score = 50  # Start neutral
        flags = []

        if not dex_data:
            return jsonify({
                'score': 0,
                'risk': 'VERY HIGH',
                'flags': ['No trading data found'],
                'recommendation': 'AVOID'
            })

        # Check buy/sell pressure
        buys = dex_data.get('buys_5m', 0)
        sells = dex_data.get('sells_5m', 0)

        if buys + sells > 0:
            buy_ratio = buys / (buys + sells)
            if buy_ratio > 0.8:
                rug_score += 20
                flags.append(f"Strong buying pressure ({buy_ratio:.1%})")
            elif buy_ratio < 0.3:
                rug_score -= 20
                flags.append(f"Heavy selling pressure ({buy_ratio:.1%})")

        # Check for extreme price movements
        price_24h = dex_data.get('price_change_24h')
        if price_24h is not None:
            if abs(price_24h) > 500:  # >500% change
                rug_score -= 30
                flags.append("Extreme volatility (>500%)")
            elif abs(price_24h) > 200:  # >200% change
                rug_score -= 15
                flags.append("High volatility (>200%)")

        # Check recent activity
        if buys + sells == 0:
            rug_score -= 25
            flags.append("No recent trading activity")
        elif buys + sells >= 10:
            rug_score += 15
            flags.append("High trading activity")

        # Determine risk level
        if rug_score >= 80:
            risk = 'LOW'
            recommendation = 'SAFE'
        elif rug_score >= 60:
            risk = 'MODERATE'
            recommendation = 'CAUTION'
        elif rug_score >= 40:
            risk = 'HIGH'
            recommendation = 'RISKY'
        else:
            risk = 'VERY HIGH'
            recommendation = 'AVOID'

        return jsonify({
            'score': max(0, min(100, rug_score)),
            'risk': risk,
            'flags': flags,
            'recommendation': recommendation,
            'price_data': dex_data
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'score': 0,
            'risk': 'UNKNOWN',
            'flags': ['Error checking token'],
            'recommendation': 'RESEARCH NEEDED'
        })

@app.route('/api/price-changes/<token_address>')
def get_price_changes(token_address):
    """Get real-time price changes"""
    dex_data = get_dexscreener_data(token_address)
    if dex_data:
        return jsonify(dex_data)
    else:
        return jsonify({'error': 'No data available'}), 404

@app.route('/api/honeypot/<token_address>')
def honeypot_analysis(token_address):
    """Comprehensive honeypot analysis for a specific token"""
    try:
        honeypot_score, honeypot_flags = filter_system.detect_honeypot_indicators(token_address)

        # Get buy/sell ratio data
        conn = filter_system.get_db_connection()
        cursor = conn.execute('''
            SELECT buys_5m, sells_5m, timestamp
            FROM price_history
            WHERE token_address = ?
            ORDER BY timestamp DESC
            LIMIT 6
        ''', (token_address,))

        recent_trades = cursor.fetchall()
        conn.close()

        total_buys = sum(row[0] for row in recent_trades if row[0] is not None)
        total_sells = sum(row[1] for row in recent_trades if row[1] is not None)

        sell_ratio = total_sells / (total_buys + total_sells) if total_buys + total_sells > 0 else 0

        # Risk assessment
        if honeypot_score >= 60:
            risk_level = "EXTREME"
            recommendation = "AVOID"
        elif honeypot_score >= 40:
            risk_level = "HIGH"
            recommendation = "VERY RISKY"
        elif honeypot_score >= 20:
            risk_level = "MODERATE"
            recommendation = "CAUTION"
        else:
            risk_level = "LOW"
            recommendation = "APPEARS SAFE"

        return jsonify({
            'token_address': token_address,
            'honeypot_score': honeypot_score,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'sell_ratio': sell_ratio,
            'total_buys': total_buys,
            'total_sells': total_sells,
            'flags': honeypot_flags,
            'analysis_timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'error': f'Honeypot analysis failed: {str(e)}',
            'token_address': token_address
        }), 500

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run(debug=True, host='0.0.0.0', port=8084)