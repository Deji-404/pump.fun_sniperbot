import sqlite3
import json
import asyncio
import websockets
from time import time
from utils import log_action_to_telegram, get_market_cap, send_telegram_message

# Maximum number of active trades
MAX_ACTIVE_TRADES = 10

# Strategy thresholds
MIN_SOL_IN_BONDING_CURVE = 10
MAX_INITIAL_BUY_PERCENTAGE = 15  # Max % of initial buy volume compared to market cap
MIN_MARKET_CAP_SOL = 10  # Minimum acceptable market cap in SOL
MAX_MARKET_CAP_SOL = 50  # Maximum acceptable market cap in SOL

# Initial trade settings
TRADE_AMOUNT = 0.01  # Amount to trade per transaction
PROFIT_TARGET_PERCENTAGE = 50
LOSS_THRESHOLD_PERCENTAGE = -50  # Maximum loss allowed before selling

# API endpoint and API key for getting token data
token_data_base_url = "https://rpc.api-pump.fun"
token_data_base_url_api_key = "your_api_key_here"

def should_buy_token(data):
    initial_buy = data.get("initialBuy", 0)
    market_cap = data.get("marketCapSol", 0)
    v_sol_in_curve = data.get("vSolInBondingCurve", 0)

    # Avoid tokens with very low or very high market cap
    if market_cap < MIN_MARKET_CAP_SOL:
        return False, "Market cap is too low, possibly risky."
    if market_cap > MAX_MARKET_CAP_SOL:
        return False, "Market cap is too high, indicating overvaluation."

    # Avoid tokens with low SOL in bonding curve
    if v_sol_in_curve < MIN_SOL_IN_BONDING_CURVE:
        return False, "Low SOL in bonding curve, insufficient liquidity."

    # Check if the initial buy volume is reasonable compared to market cap
    initial_buy_percentage = (
        initial_buy / (market_cap * 1e9)
    ) * 100  # Convert market cap to lamports
    if initial_buy_percentage > MAX_INITIAL_BUY_PERCENTAGE:
        return (
            False,
            f"Initial buy volume too high ({initial_buy_percentage:.2f}% of market cap).",
        )

    # If all checks pass, it's safe to buy
    return True, "Token passed all the tests and looks safe to buy."

# Function to track bought tokens in the database
def track_bought_token(token_data, buy_price, quantity, target_price):
    with setup_database() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO active_trades (token_name, mint_address, buy_price, sell_price, target_price, quantity, buy_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (token_data['name'], token_data['mint'], buy_price, 0, target_price, quantity, time(), 'active'))
        log_action_to_telegram(f"Tracked token {token_data['name']} with buy price {buy_price} SOL and target price {target_price} SOL")

# WebSocket subscription to detect new tokens
async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"method": "subscribeNewToken"}))
        async for message in websocket:
            data = json.loads(message)
            if "message" in data:
                print("Received Message:", data)
            else:
                print("New Token Created:", data)  # Debugging

                # Apply buy strategy to the token
                buy_decision, decision_reason = should_buy_token(data)

                decision_text = "Safe to buy" if buy_decision else "Not safe to buy"

                # Send the token details to Telegram, including the decision and reason
                send_telegram_message(data, decision_text, decision_reason)
 
                buy_decision, reason = should_buy_token(data)
                if count_active_trades() < MAX_ACTIVE_TRADES and buy_decision:
                    mint_address = data.get('mint')
                    print(mint_address)
                    buy_price = get_market_cap(mint_address)
                    target_price = buy_price * (1 + PROFIT_TARGET_PERCENTAGE / 100)
                    track_bought_token(data, buy_price, TRADE_AMOUNT, target_price)
                    log_action_to_telegram(f"Buy order placed for token {data['name']} at marketCap {buy_price}")

# Database setup
def setup_database():
    conn = sqlite3.connect('tokens.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS active_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_name TEXT,
            mint_address TEXT,
            buy_price REAL,
            sell_price REAL,
            target_price REAL,
            quantity REAL,
            buy_time TIMESTAMP,
            status TEXT
        )
    ''')
    return conn

# Function to count active trades
def count_active_trades():
    conn = setup_database()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM active_trades WHERE status = "active"')
    active_trade_count = cursor.fetchone()[0]
    conn.close()
    return active_trade_count

# Run simulation
while True:
    asyncio.get_event_loop().run_until_complete(subscribe())
