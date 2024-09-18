import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the credentials
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_ACTION_ID = os.getenv('TELEGRAM_ACTION_ID')

# Function to convert SOL to USD
def convert_sol_to_usd(sol_amount):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
    response = requests.get(url, timeout=60)
    sol_price_in_usd = response.json()['solana']['usd']
    return sol_amount * sol_price_in_usd


# Function to format the token data and include the decision
def format_token_data(data, decision, reason):
    formatted_message = (
        f"🚀 **New Token Created on Pump.Fun!** 🚀\n\n"
        f"🔹 **Token Name**: {data.get('name', 'Unknown')}\n"
        f"🔹 **Symbol**: `{data.get('symbol', 'N/A')}`\n"
        f"🔹 **Mint Address**: `{data.get('mint', 'N/A')}`\n"
        f"🔹 **Trader Public Key**: `{data.get('traderPublicKey', 'N/A')}`\n"
        f"🔹 **Transaction Type**: `{data.get('txType', 'N/A').capitalize()}`\n"
        f"🔹 **Initial Buy Volume**: `{data.get('initialBuy', 0):.2f}` tokens 🪙\n\n"
        f"📊 **Bonding Curve Details**:\n"
        f"   • **vTokens in Bonding Curve**: `{data.get('vTokensInBondingCurve', 0):.2f}` tokens 🟢\n"
        f"   • **vSOL in Bonding Curve**: `{data.get('vSolInBondingCurve', 0):.2f}` SOL 💰\n"
        f"   • **Market Cap**: `{data.get('marketCapSol', 0):.2f}` SOL 📈\n\n"
        f"💡 **Buy Decision**: {decision} { '🟢' if decision == 'Safe to buy' else '🔴' }\n"
        f"📝 **Reason**: {reason}\n\n"
        f"🔗 **Token Metadata URI**: [View Metadata]({data.get('uri', 'N/A')})\n"
        f"🔗 **View Transaction**: [Solscan Link](https://solscan.io/tx/{data.get('signature', 'N/A')})\n"
    )
    return formatted_message

# Function to send a message to the new token Telegram group
def send_telegram_message(token_data, decision, reason):
    message = format_token_data(token_data, decision, reason)
    # print("Formatted Message:", message)  # Debugging

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",  # Enables bold, italics, links, etc.
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Message sent successfully to Telegram group.")
        else:
            print(f"Failed to send message: {response.status_code}")
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")

# Log action to Telegram
def log_action_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_ACTION_ID, 'text': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload, timeout=60)


# Function to get the market cap from the token's webpage
def get_market_cap(token_contract):
    token_url = f"https://pump.fun/{token_contract}"
    response = requests.get(token_url, timeout=60)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        market_cap_element = soup.find('div', class_='text-sm text-green-300 flex gap-2')
        if market_cap_element:
            market_cap = market_cap_element.text.replace('Market cap: $', '').replace(',', '').strip()
            return float(market_cap)
    return None
