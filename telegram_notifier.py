import requests
from datetime import datetime, timedelta
from google_sheets import open_spreadsheet
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN not loaded")

SPREADSHEET_ID = "1wGnF_bV3pNMx2l3BtwXEfKFdbs3ToYsgxqqgnKBAqgU"

# timings
ATTENDANCE_REMINDER_MINUTES = 5

def send_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": message
    })

def attendance_reminders(sheet):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    timetable = sheet.worksheet("Timetable").get_all_records()
    attendance = sheet.worksheet("Attendance").get_all_records()
    settings = sheet.worksheet("Notification_Settings").get_all_records()

    for lec in timetable:
        end = datetime.strptime(
            f"{today} {lec['end_time']}", "%Y-%m-%d %H:%M"
        )

        if 0 <= (now - end).total_seconds() <= ATTENDANCE_REMINDER_MINUTES * 60:

            marked = any(
                a for a in attendance
                if str(a["user_id"]) == str(lec["user_id"])
                and a["date"] == today
                and a["subject"] == lec["subject"]
                and a["start_time"] == lec["start_time"]
            )

            if not marked:
                for s in settings:
                    if (
                        str(s["user_id"]) == str(lec["user_id"])
                        and s["telegram"] == "yes"
                        and s.get("telegram_chat_id")
                    ):
                        send_telegram(
                            s["telegram_chat_id"],
                            f"⚠️ *Attendance Reminder*\n\n"
                            f"📘 {lec['subject']}\n"
                            f"🕒 {lec['start_time']} – {lec['end_time']}\n\n"
                            f"Please mark your attendance."
                        )

if __name__ == "__main__":
    sheet = open_spreadsheet(SPREADSHEET_ID)

    attendance_reminders(sheet)

