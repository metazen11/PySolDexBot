import os
import sqlite3
from datetime import datetime, timedelta
import traceback
import requests
import json
import logging
from typing import List, Dict
import http.server
import socketserver
import time
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey
import aiohttp
import asyncio
import sys

# Configuration
RAYDIUM_API_ENDPOINT = 'https://api.raydium.io/v2/main/pairs'
SOLANA_RPC_ENDPOINT = 'https://api.mainnet-beta.solana.com'
SOLSCAN_API_ENDPOINT = 'https://public-api.solscan.io/account/transactions'
CHECK_INTERVAL = 60  # Check every 60 seconds
DATABASE_FILE = 'raydium_pools.db'
TELEGRAM_BOT_TOKEN = os.getenv('TG_API_KEY')
TELEGRAM_CHAT_ID = os.getenv('TG_CHAT_ID')
HTML_FILE = 'pools.html'
PORT = 8000

SOL_ADDRESS = "So11111111111111111111111111111111111111112"

# Set up logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Register adapter to handle datetime with sqlite3
def adapt_datetime(ts):
    return ts.strftime('%Y-%m-%d %H:%M:%S')

def convert_datetime(ts):
    return datetime.strptime(ts.decode('utf-8'), '%Y-%m-%d %H:%M:%S')

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

def fetch_raydium_pools() -> List[Dict]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(RAYDIUM_API_ENDPOINT, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        logging.error(f"Failed to fetch Raydium pools: {e}")
        return []

def create_table():
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    # Create the table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS pools
                 (lp_mint TEXT PRIMARY KEY, 
                  name TEXT, 
                  liquidity REAL, 
                  volume24h REAL, 
                  created_at TIMESTAMP,
                  is_new INTEGER)''')

    # Check if the new columns exist, if not, add them
    c.execute("PRAGMA table_info(pools)")
    columns = [column[1] for column in c.fetchall()]

    if 'token_address' not in columns:
        c.execute("ALTER TABLE pools ADD COLUMN token_address TEXT")

    if 'is_pump_token' not in columns:
        c.execute("ALTER TABLE pools ADD COLUMN is_pump_token INTEGER")

    if 'discovered_at' not in columns:
        c.execute("ALTER TABLE pools ADD COLUMN discovered_at TIMESTAMP")

    conn.commit()
    conn.close()

def save_pool(pool: Dict):
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    token_address = pool['quoteMint'] if pool['baseMint'] == SOL_ADDRESS else pool['baseMint']
    current_time = datetime.now()

    # Check if pool already exists
    c.execute('SELECT lp_mint, discovered_at FROM pools WHERE lp_mint = ?', (pool['lpMint'],))
    existing = c.fetchone()

    if existing:
        # Update existing pool but keep original discovered_at
        c.execute('''
            UPDATE pools
            SET name = ?, liquidity = ?, volume24h = ?, created_at = ?, is_new = 0
            WHERE lp_mint = ?
        ''', (
            pool['name'],
            pool['liquidity'],
            pool['volume24h'],
            current_time,
            pool['lpMint']
        ))
    else:
        # Insert new pool with current time as discovered_at
        c.execute('''
            INSERT INTO pools
            (lp_mint, name, liquidity, volume24h, created_at, is_new, token_address, is_pump_token, discovered_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
        ''', (
            pool['lpMint'],
            pool['name'],
            pool['liquidity'],
            pool['volume24h'],
            current_time,
            token_address,
            token_address.lower().endswith('pump'),
            current_time
        ))

    conn.commit()
    conn.close()

def get_top_pools(limit: int = 100, include_last_hour: bool = True) -> List[tuple]:
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    one_hour_ago = datetime.now() - timedelta(hours=1)

    if include_last_hour:
        c.execute('''
            SELECT * FROM pools 
            WHERE discovered_at > ?
            UNION
            SELECT * FROM pools 
            ORDER BY volume24h DESC 
            LIMIT ?
        ''', (one_hour_ago, limit))
    else:
        c.execute('''
            SELECT * FROM pools 
            ORDER BY volume24h DESC 
            LIMIT ?
        ''', (limit,))

    pools = c.fetchall()
    conn.close()

    return pools

def load_stored_pools() -> set:
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute('SELECT lp_mint FROM pools')
    stored_pools = set(row[0] for row in c.fetchall())
    conn.close()
    return stored_pools

def find_new_pools(current_pools: List[Dict], stored_pools: set) -> List[Dict]:
    return [pool for pool in current_pools if pool['lpMint'] not in stored_pools]

def mark_pools_as_old():
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute('UPDATE pools SET is_new = 0')
    conn.commit()
    conn.close()

def get_new_untradable_pools():
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    # Get pools created in the last hour with low volume (potentially new/untradable)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    c.execute('''
        SELECT lp_mint, name, liquidity, volume24h, created_at, token_address
        FROM pools
        WHERE discovered_at > ? AND volume24h < 1000
        ORDER BY discovered_at DESC
    ''', (one_hour_ago,))

    pools = []
    for row in c.fetchall():
        pools.append({
            'lp_mint': row[0],
            'name': row[1],
            'liquidity': row[2],
            'volume24h': row[3],
            'created_at': row[4],
            'token_address': row[5]
        })

    conn.close()
    return pools

async def check_recent_transactions(token_address: str) -> bool:
    try:
        params = {
            'account': token_address,
            'limit': 5
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(SOLSCAN_API_ENDPOINT, params=params) as response:
                response.raise_for_status()
                transactions = await response.json()

        if transactions:
            latest_transaction_time = datetime.fromtimestamp(transactions[0]['blockTime'])
            return (datetime.now() - latest_transaction_time) <= timedelta(hours=1)

        return False
    except Exception as e:
        logging.error(f"Failed to fetch transactions for {token_address}: {e}")
        return False

def send_telegram_message(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to send Telegram message: {e}")
    else:
        logging.warning("Telegram bot token or chat ID not set. Skipping Telegram notification.")

def export_pools_to_html(pools):
    html_content = """
    <html>
    <head>
        <title>Raydium Pools</title>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid black; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Raydium Pools</h1>
        <table>
            <tr>
                <th>Name</th>
                <th>Liquidity</th>
                <th>Volume (24h)</th>
                <th>LP Mint Address</th>
                <th>Token Address</th>
                <th>Created At</th>
                <th>Is New</th>
                <th>Is Pump Token</th>
            </tr>
    """
    for pool in pools:
        html_content += f"""
            <tr>
                <td>{pool[1]}</td>
                <td>{pool[2]}</td>
                <td>{pool[3]}</td>
                <td>{pool[0]}</td>
                <td>{pool[6]}</td>
                <td>{pool[4]}</td>
                <td>{"Yes" if pool[5] else "No"}</td>
                <td>{"Yes" if pool[7] else "No"}</td>
            </tr>
        """
    html_content += """
        </table>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w') as f:
        f.write(html_content)

async def check_new_raydium_pools():
    try:
        current_pools = fetch_raydium_pools()
        logging.info(f"Current pools fetched: {len(current_pools)}")

        for pool in current_pools:
            save_pool(pool)

        new_untradable_pools = get_new_untradable_pools()

        if new_untradable_pools:
            logging.info(f"Found {len(new_untradable_pools)} new untradable pool(s). Checking first 5:")
            for pool in new_untradable_pools[:5]:  # Limit to first 5
                authorities = await check_token_authorities(pool['token_address'])
                if not authorities['has_mint_authority'] and not authorities['has_freeze_authority']:
                    logging.info(f"Name: {pool['name']}")
                    logging.info(f"LP Mint: {pool['lp_mint']}")
                    logging.info(f"Token Address: {pool['token_address']}")
                    logging.info(f"Created at: {pool['created_at']}")
                    logging.info("-------------------------")
                else:
                    logging.warning(f"Potential risky token detected: {pool['name']} ({pool['token_address']})")
                    if authorities['has_mint_authority']:
                        logging.warning("- Has mint authority")
                    if authorities['has_freeze_authority']:
                        logging.warning("- Has freeze authority")

        logging.info("Checking for active trading on existing pools (first 5)...")
        conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute('SELECT token_address, name FROM pools WHERE volume24h > 0 LIMIT 5')  # Limit to first 5
        existing_pools = c.fetchall()
        conn.close()

        for token_address, name in existing_pools:
            if await check_recent_transactions(token_address):
                authorities = await check_token_authorities(token_address)
                if not authorities['has_mint_authority'] and not authorities['has_freeze_authority']:
                    logging.info(f"Active trading detected for {name} ({token_address})")
                else:
                    logging.warning(f"Active trading on potential risky token: {name} ({token_address})")
                    if authorities['has_mint_authority']:
                        logging.warning("- Has mint authority")
                    if authorities['has_freeze_authority']:
                        logging.warning("- Has freeze authority")

    except Exception as e:
        logging.error(f"Error checking new Raydium pools: {e}")
        logging.error(traceback.format_exc())

async def check_token_authorities(token_address: str) -> Dict[str, bool]:
    async with AsyncClient(SOLANA_RPC_ENDPOINT) as client:
        try:
            pubkey = Pubkey.from_string(token_address)
            resp = await client.get_account_info(pubkey, commitment=Confirmed)
            if resp.value:
                data = resp.value.data
                # Parse the token data
                # Note: This is a simplified check and might need adjustment based on the exact token program structure
                mint_authority = int.from_bytes(data[4:4+32], 'little') != 0
                freeze_authority = int.from_bytes(data[36:36+32], 'little') != 0
                return {
                    "has_mint_authority": mint_authority,
                    "has_freeze_authority": freeze_authority
                }
            else:
                logging.warning(f"No account info found for token {token_address}")
                return {"has_mint_authority": False, "has_freeze_authority": False}
        except Exception as e:
            logging.error(f"Error checking authorities for token {token_address}: {e}")
            return {"has_mint_authority": False, "has_freeze_authority": False}

def start_http_server():
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        logger.info(f"Serving at port {PORT}")
        httpd.serve_forever()

async def main_loop():
    create_table()
    while True:
        await check_new_raydium_pools()
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
