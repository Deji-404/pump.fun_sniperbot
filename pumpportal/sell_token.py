import sqlite3
from utils import log_action_to_telegram, get_market_cap

# Telegram and trading settings
TELEGRAM_BOT_TOKEN = "your_token_here"
TELEGRAM_ACTION_ID = "your_action_chat_id_here"
PROFIT_TARGET_PERCENTAGE = 50
LOSS_THRESHOLD_PERCENTAGE = -50

# Setup database for token tracking
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


# Function to monitor tokens and sell based on profit/loss
def monitor_tokens_for_sale():
    with setup_database() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM active_trades WHERE status = "active"')
        tokens = cursor.fetchall()

        for token in tokens:
            token_name = token[1]
            mint_address = token[2]
            buy_price = token[3]

            current_market_cap = get_market_cap(mint_address)
            if current_market_cap:
                percentage_change = ((current_market_cap - buy_price) / buy_price) * 100

                if percentage_change > 1:
                    print(f"Profit of {percentage_change}% made on {token_name} of mint {mint_address}")
                else:
                    print(f"Loss of {percentage_change}% made on {token_name} of mint {mint_address}")

                print(current_market_cap, buy_price)
                print('---------------------------------------------------------------------------------------------------------\n\n')


                if percentage_change >= PROFIT_TARGET_PERCENTAGE:
                    log_action_to_telegram(f"💰 Profit target reached for {token[1]} ({percentage_change:.2f}%), placing sell order...")
                    cursor.execute('UPDATE active_trades SET status = ?, sell_price = ? WHERE mint_address = ?', ('sold', current_market_cap, mint_address))
                    conn.commit()
                elif percentage_change <= LOSS_THRESHOLD_PERCENTAGE:
                    log_action_to_telegram(f"⚠️ Loss threshold reached for {token[1]} ({percentage_change:.2f}%), placing sell order...")
                    cursor.execute('UPDATE active_trades SET status = ?, sell_price = ? WHERE mint_address = ?', ('sold', current_market_cap, mint_address))
                    conn.commit()


# Monitor and act on token sales
while True:
    monitor_tokens_for_sale()
