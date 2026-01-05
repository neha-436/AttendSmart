import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from google_sheets import open_spreadsheet

# ================= LOAD ENV =================

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN not loaded")

SPREADSHEET_ID = "1wGnF_bV3pNMx2l3BtwXEfKFdbs3ToYsgxqqgnKBAqgU"
spreadsheet = open_spreadsheet(SPREADSHEET_ID)

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to AttendSmart Bot!\n\n"
        "Your account is already linked automatically.\n"
        "You will receive notifications based on your settings."
    )

# (Optional: keep /link only if you REALLY need it)
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Linking is handled automatically from the app."
    )

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))

    print("🤖 AttendSmart bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
