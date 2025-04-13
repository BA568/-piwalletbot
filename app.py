import os
import time
import json
import requests
import logging
from threading import Thread
from flask import Flask, render_template_string
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALERT_USER = os.getenv("ALERT_USER")
WALLET_FILE = "wallets.json"
LOG_FILE = "airdrop_log.txt"

bot = Bot(token=BOT_TOKEN)
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_web = Flask(__name__)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')
balances = {}

def get_balance(wallet):
    try:
        url = f"https://blockexplorer.minepi.com/api/accounts/{wallet.strip()}"
        response = requests.get(url)
        if response.status_code == 200:
            return round(float(response.json().get("balance", 0)), 6)
    except:
        pass
    return None

def load_wallets():
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, "r") as f:
            return json.load(f)
    return []

def save_wallets(wallets):
    with open(WALLET_FILE, "w") as f:
        json.dump(wallets, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👑 *Welcome to Pi Wallet Bot Manual*

"
        "🧾 *Available Commands:*
"
        "➡️ `/addwallet WALLET` - Start tracking a wallet
"
        "➡️ `/removewallet WALLET` - Stop tracking a wallet
"
        "➡️ `/listwallets` - Show all tracked wallets
"
        "➡️ `/help` - Show this manual

"
        "📡 Live alerts + dashboard enabled 👁️"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def addwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /addwallet WALLET_ADDRESS")
        return
    wallet = context.args[0]
    wallets = load_wallets()
    if wallet not in wallets:
        wallets.append(wallet)
        save_wallets(wallets)
        await update.message.reply_text(f"✅ Now tracking: {wallet}")
    else:
        await update.message.reply_text("🟡 Already tracking that wallet.")

async def removewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /removewallet WALLET_ADDRESS")
        return
    wallet = context.args[0]
    wallets = load_wallets()
    if wallet in wallets:
        wallets.remove(wallet)
        save_wallets(wallets)
        await update.message.reply_text(f"❌ Removed from tracking: {wallet}")
    else:
        await update.message.reply_text("🚫 Wallet not found in tracking list.")

async def listwallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallets = load_wallets()
    if not wallets:
        await update.message.reply_text("🪹 No wallets are currently being tracked.")
        return
    msg = "📄 *Currently Tracked Wallets:*
"
    for w in wallets:
        msg += f"• `{w}`
"
    await update.message.reply_text(msg, parse_mode='Markdown')

def monitor_wallets():
    global balances
    print("🛰️ Combined Bot + Dashboard Running...")
    while True:
        wallets = load_wallets()
        for wallet in wallets:
            current = get_balance(wallet)
            previous = balances.get(wallet, 0)
            if current is not None:
                if current > previous:
                    delta = round(current - previous, 6)
                    msg = f"📬 *Incoming Pi Detected!*
Wallet: `{wallet}`
💹 +{delta} Pi received
New Balance: `{current}` Pi"
                    bot.send_message(chat_id=ALERT_USER, text=msg, parse_mode='Markdown')
                    logging.info(f"[{wallet}] Airdrop: +{delta} Pi | New balance: {current}")
                balances[wallet] = current
        time.sleep(5)

@app_web.route("/")
def dashboard():
    wallets = load_wallets()
    live_data = [(w, get_balance(w)) for w in wallets]
    return render_template_string("""
        <html>
        <head>
            <title>Pi Dashboard</title>
            <style>
                body { background:#111; color:#fff; font-family:Arial; padding:20px; }
                table { width:100%; border-collapse:collapse; }
                th, td { border:1px solid #444; padding:10px; }
                th { background:#222; }
                tr:nth-child(even) { background:#1c1c1c; }
            </style>
        </head>
        <body>
            <h2>📊 Pi Wallet Dashboard</h2>
            <table><tr><th>Wallet</th><th>Balance</th></tr>
            {% for w, b in data %}
            <tr><td>{{ w }}</td><td>{{ b }}</td></tr>
            {% endfor %}
            </table>
            <script>setTimeout(()=>location.reload(), 10000);</script>
        </body>
        </html>
    """, data=live_data)

def run():
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("help", help_cmd))
    app_telegram.add_handler(CommandHandler("addwallet", addwallet))
    app_telegram.add_handler(CommandHandler("removewallet", removewallet))
    app_telegram.add_handler(CommandHandler("listwallets", listwallets))
    Thread(target=lambda: app_telegram.run_polling(), daemon=True).start()
    Thread(target=monitor_wallets, daemon=True).start()
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    run()
