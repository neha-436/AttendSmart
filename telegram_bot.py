import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I am AttendSmart Bot.\n\n"
        "I’ll send you lecture reminders and notifications.\n\n"
        "Please link your account in the AttendSmart app."
    )

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 Telegram bot running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
