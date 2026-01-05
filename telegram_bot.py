import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN not loaded")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "attendsmart-482611-d4e53c2dabec.json",
    scopes=SCOPES
)

gc = gspread.authorize(creds)

SPREADSHEET_ID = "1wGnF_bV3pNMx2l3BtwXEfKFdbs3ToYsgxqqgnKBAqgU"


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I am AttendSmart Bot.\n\n"
        "I’ll send you lecture reminders and notifications.\n\n"
        "Please link your account in the AttendSmart app."
    )

# /link command
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please send:\n/link AS-1234")
        return

    link_code = context.args[0]
    chat_id = update.effective_chat.id

    sheet = gc.open_by_key(SPREADSHEET_ID)
    ws = sheet.worksheet("Notification_Settings")

    rows = ws.get_all_records()
    headers = ws.row_values(1)

    matched = False

    for idx, row in enumerate(rows, start=2):
        if row.get("telegram_code") == link_code:
            ws.update_cell(idx, headers.index("telegram_chat_id") + 1, str(chat_id))
            ws.update_cell(idx, headers.index("telegram") + 1, "yes")
            ws.update_cell(idx, headers.index("telegram_code") + 1, "")
            matched = True
            break

    if matched:
        await update.message.reply_text(
            "✅ Telegram linked successfully!\nYou will now receive notifications."
        )
    else:
        await update.message.reply_text(
            "❌ Invalid or expired linking code.\nPlease regenerate it from the app."
        )



# def run_bot():
#     app = ApplicationBuilder().token(BOT_TOKEN).build()
#     app.add_handler(CommandHandler("start", start))
#     print("🤖 Telegram bot running...")
#     app.run_polling()

# if __name__ == "__main__":
#     run_bot()

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link)) 

    print("🤖 Telegram bot running...")
    app.run_polling()
