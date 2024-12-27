from typing import Dict, Optional
import aiohttp
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenAPIChecker:
    def __init__(self, config: Dict):
        self.config = config
        self.helius_api_key = config['helius_api_key']
        self.birdeye_api_key = config['birdeye_api_key']
        self.dexscreener_api_key = config.get('dexscreener_api_key')  # Optional
        self.session = None

    async def initialize(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def check_token(self, token_address: str) -> Dict:
        """Comprehensive token check using multiple APIs"""
        try:
            # Run all API checks concurrently
            results = await asyncio.gather(
                self._check_helius(token_address),
                self._check_birdeye(token_address),
                self._check_dexscreener(token_address),
                return_exceptions=True
            )

            # Combine and analyze results
            combined_data = self._combine_api_results(results)
            risk_score = self._calculate_risk_score(combined_data)

            return {
                'token_address': token_address,
                'risk_score': risk_score,
                'data': combined_data,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error checking token {token_address}: {e}")
            return {'error': str(e)}

    async def _check_helius(self, token_address: str) -> Dict:
        """Check token using Helius API"""
        try:
            url = f"https://api.helius.xyz/v0/token-metadata?api-key={self.helius_api_key}"
            async with self.session.get(url, params={'tokenAddress': token_address}) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract key metrics
                    return {
                        'source': 'helius',
                        'metadata': data.get('metadata', {}),
                        'mint_authority': data.get('onChainMetadata', {}).get('mintAuthority'),
                        'freeze_authority': data.get('onChainMetadata', {}).get('freezeAuthority'),
                        'supply': data.get('onChainMetadata', {}).get('supply'),
                    }
                else:
                    logger.warning(f"Helius API error: {response.status}")
                    return {'source': 'helius', 'error': f"Status {response.status}"}

        except Exception as e:
            logger.error(f"Helius API error: {e}")
            return {'source': 'helius', 'error': str(e)}

    async def _check_birdeye(self, token_address: str) -> Dict:
        """Check token using Birdeye API"""
        try:
            headers = {'X-API-KEY': self.birdeye_api_key}
            url = f"https://public-api.birdeye.so/public/tokeninfo?address={token_address}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'source': 'birdeye',
                        'price': data.get('price'),
                        'volume_24h': data.get('volume24h'),
                        'mcap': data.get('mcap'),
                        'holder_count': data.get('holderCount'),
                        'transfers_24h': data.get('transfers24h'),
                    }
                else:
                    logger.warning(f"Birdeye API error: {response.status}")
                    return {'source': 'birdeye', 'error': f"Status {response.status}"}

        except Exception as e:
            logger.error(f"Birdeye API error: {e}")
            return {'source': 'birdeye', 'error': str(e)}

    async def _check_dexscreener(self, token_address: str) -> Dict:
        """Check token using DexScreener API"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if not pairs:
                        return {
                            'source': 'dexscreener',
                            'error': 'No trading pairs found'
                        }

                    # Get the most liquid pair
                    main_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
                    
                    return {
                        'source': 'dexscreener',
                        'price_usd': main_pair.get('priceUsd'),
                        'liquidity_usd': main_pair.get('liquidity', {}).get('usd'),
                        'volume_24h': main_pair.get('volume', {}).get('h24'),
                        'price_change_24h': main_pair.get('priceChange', {}).get('h24'),
                        'created_at': main_pair.get('createAt'),
                    }
                else:
                    logger.warning(f"DexScreener API error: {response.status}")
                    return {'source': 'dexscreener', 'error': f"Status {response.status}"}

        except Exception as e:
            logger.error(f"DexScreener API error: {e}")
            return {'source': 'dexscreener', 'error': str(e)}

    def _combine_api_results(self, results: list) -> Dict:
        """Combine and normalize data from different APIs"""
        combined = {}
        
        for result in results:
            if isinstance(result, Exception):
                continue
                
            source = result.get('source')
            if source:
                combined[source] = result

        return combined

    def _calculate_risk_score(self, data: Dict) -> float:
        """Calculate risk score based on API data"""
        score = 0
        max_score = 0
        
        # Check Helius data
        if 'helius' in data and 'error' not in data['helius']:
            max_score += 30
            helius_data = data['helius']
            
            # Check mint authority
            if not helius_data.get('mint_authority'):
                score += 10  # No mint authority is good
            
            # Check freeze authority
            if not helius_data.get('freeze_authority'):
                score += 10  # No freeze authority is good
                
            # Check metadata
            if helius_data.get('metadata'):
                score += 10  # Has proper metadata

        # Check Birdeye data
        if 'birdeye' in data and 'error' not in data['birdeye']:
            max_score += 40
            birdeye_data = data['birdeye']
            
            # Check holders
            holders = birdeye_data.get('holder_count', 0)
            if holders >= 1000:
                score += 15
            elif holders >= 500:
                score += 10
            elif holders >= 200:
                score += 5
                
            # Check volume
            volume = float(birdeye_data.get('volume_24h', 0))
            if volume >= 100000:  # $100k daily volume
                score += 15
            elif volume >= 50000:
                score += 10
            elif volume >= 10000:
                score += 5
                
            # Check transfers
            transfers = birdeye_data.get('transfers_24h', 0)
            if transfers >= 1000:
                score += 10
            elif transfers >= 500:
                score += 5

        # Check DexScreener data
        if 'dexscreener' in data and 'error' not in data['dexscreener']:
            max_score += 30
            dex_data = data['dexscreener']
            
            # Check liquidity
            liquidity = float(dex_data.get('liquidity_usd', 0))
            if liquidity >= 100000:  # $100k liquidity
                score += 15
            elif liquidity >= 50000:
                score += 10
            elif liquidity >= 10000:
                score += 5
                
            # Check age
            created_at = dex_data.get('created_at')
            if created_at:
                age_days = (datetime.now() - datetime.fromtimestamp(created_at)).days
                if age_days >= 30:
                    score += 15
                elif age_days >= 7:
                    score += 10
                elif age_days >= 3:
                    score += 5

        # Convert to percentage
        return (score / max_score * 100) if max_score > 0 else 0