import os
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7557926144:AAH3bBKcAoLgO5KTHWjXWmHY9Q3Rm5FM6u0"
ALERT_USER = "@Banky664"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Pi Bot is online and ready, King!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("✅ Bot started. Awaiting commands...")
    app.run_polling()