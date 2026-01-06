import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from google_sheets import open_spreadsheet
from holidays import is_today_national_holiday, is_today_user_holiday

# ================== ENV ==================

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN not loaded")

# ================== CONFIG ==================

SPREADSHEET_ID = "1wGnF_bV3pNMx2l3BtwXEfKFdbs3ToYsgxqqgnKBAqgU"

ATTENDANCE_REMINDER_MINUTES = 5        # After lecture end
TIMETABLE_REMINDER_HOUR = 21           # 9 PM
TIMETABLE_REMINDER_MINUTE = 0

MIN_ATTENDANCE_REQUIRED = 75

# ================== RUNTIME CACHE ==================

attendance_sent_cache = set()
timetable_sent_cache = set()

# ================== TELEGRAM ==================

def send_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=5)
    except Exception as e:
        print("Telegram error:", e)



# ================== ATTENDANCE REMINDER ==================

def attendance_reminders(sheet):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    today_day = now.strftime("%A")

    if is_today_national_holiday(sheet):
        return

    timetable = sheet.worksheet("Timetable").get_all_records()
    attendance = sheet.worksheet("Attendance").get_all_records()
    settings = sheet.worksheet("Notification_Settings").get_all_records()

    for lec in timetable:
        user_id = lec["user_id"]

        if is_today_user_holiday(sheet, user_id):
            continue

        if lec["day"] != today_day:
            continue

        end_time = datetime.strptime(
            f"{today} {lec['end_time']}", "%Y-%m-%d %H:%M"
        )

        delta = (now - end_time).total_seconds()

        if not (0 <= delta <= ATTENDANCE_REMINDER_MINUTES * 60):
            continue

        key = (user_id, lec["subject"], lec["start_time"], today)
        if key in attendance_sent_cache:
            continue

        already_marked = any(
            a for a in attendance
            if str(a["user_id"]) == str(user_id)
            and a["date"] == today
            and a["subject"] == lec["subject"]
            and a["start_time"] == lec["start_time"]
        )

        if already_marked:
            continue

        for s in settings:
            if (
                str(s["user_id"]) == str(user_id)
                and s["telegram"] == "yes"
                and s.get("telegram_chat_id")
            ):
                send_telegram(
                    s["telegram_chat_id"],
                    f"⚠️ *Attendance Reminder*\n\n"
                    f"📘 *{lec['subject']}*\n"
                    f"🕒 {lec['start_time']} – {lec['end_time']}\n\n"
                    f"Please mark your attendance."
                )
                attendance_sent_cache.add(key)


# ================== NEXT-DAY TIMETABLE ==================

def timetable_reminders(sheet):
    now = datetime.now()

    if now.hour != TIMETABLE_REMINDER_HOUR or now.minute != TIMETABLE_REMINDER_MINUTE:
        return

    tomorrow = now + timedelta(days=1)
    tomorrow_day = tomorrow.strftime("%A")
    tomorrow_date = tomorrow.strftime("%Y-%m-%d")

    if is_today_national_holiday(sheet, date=tomorrow):
        return

    timetable = sheet.worksheet("Timetable").get_all_records()
    settings = sheet.worksheet("Notification_Settings").get_all_records()

    users = set(str(l["user_id"]) for l in timetable)

    for user_id in users:
        if is_today_user_holiday(sheet, user_id, date=tomorrow):
            continue

        lectures = [
            l for l in timetable
            if str(l["user_id"]) == str(user_id)
            and l["day"] == tomorrow_day
        ]

        if not lectures:
            continue

        key = (user_id, tomorrow_date)
        if key in timetable_sent_cache:
            continue

        message = f"📅 *Tomorrow's Timetable ({tomorrow_day})*\n\n"
        for lec in lectures:
            message += (
                f"📘 {lec['subject']}\n"
                f"🕒 {lec['start_time']} – {lec['end_time']}\n\n"
            )

        for s in settings:
            if (
                str(s["user_id"]) == str(user_id)
                and s["telegram"] == "yes"
                and s.get("telegram_chat_id")
            ):
                send_telegram(s["telegram_chat_id"], message)
                timetable_sent_cache.add(key)


def get_semester_dates(sheet, user_id):
    ws = sheet.worksheet("Semester")
    rows = ws.get_all_records()

    for r in rows:
        if str(r["user_id"]) == str(user_id):
            start = datetime.strptime(r["semester_start"], "%Y-%m-%d").date()
            end = datetime.strptime(r["semester_end"], "%Y-%m-%d").date()
            return start, end

    raise ValueError(f"Semester dates not set for user {user_id}")



# ================== ATTENDANCE CALCULATION ==================

def calculate_attendance(sheet, user_id):
    timetable = sheet.worksheet("Timetable").get_all_records()
    attendance = sheet.worksheet("Attendance").get_all_records()

    semester_start, semester_end = get_semester_dates(sheet, user_id)
    today = min(datetime.now().date(), semester_end)

    total_lectures = 0
    present = 0

    for lec in timetable:
        if str(lec["user_id"]) != str(user_id):
            continue

        current_date = semester_start

        while current_date <= today:
            if current_date.strftime("%A") != lec["day"]:
                current_date += timedelta(days=1)
                continue

            # Skip holidays
            if is_today_national_holiday(sheet, date=current_date):
                current_date += timedelta(days=1)
                continue

            if is_today_user_holiday(sheet, user_id, date=current_date):
                current_date += timedelta(days=1)
                continue


            total_lectures += 1

            record = next(
                (a for a in attendance
                if str(a["user_id"]) == str(user_id)
                and a["date"] == current_date.strftime("%Y-%m-%d")
                and a["subject"] == lec["subject"]
                and a["start_time"] == lec["start_time"]),
                None
            )

            # Skip OFF lectures completely
            if record and record["status"] == "Off":
                current_date += timedelta(days=1)
                continue

            total_lectures += 1

            if record and record["status"] == "Yes":
                present += 1


            current_date += timedelta(days=1)

    # ---- ZERO ATTENDANCE GUARD ----
    if total_lectures == 0:
        return {
            "attendance_pct": 0,
            "present": 0,
            "total": 0
        }

    attendance_pct = round((present / total_lectures) * 100, 2)

    return {
        "attendance_pct": attendance_pct,
        "present": present,
        "total": total_lectures
    }




# ================== RISK PREDICTION ==================

def predict_risk(sheet, user_id, minimum_required=75):
    stats = calculate_attendance(sheet, user_id)

    present = stats["present"]
    total = stats["total"]

    # ---- ZERO ATTENDANCE GUARD ----
    if total == 0:
        return {
            "current_pct": 0,
            "projected_pct": 0,
            "future_lectures": 0,
            "risk": "UNKNOWN",
            "message": "Not enough attendance data yet."
        }

    current_pct = stats["attendance_pct"]


    timetable = sheet.worksheet("Timetable").get_all_records()
    semester_start, semester_end = get_semester_dates(sheet, user_id)

    today = datetime.now().date()
    future_lectures = 0

    for lec in timetable:
        if str(lec["user_id"]) != str(user_id):
            continue

        date_ptr = today + timedelta(days=1)

        while date_ptr <= semester_end:
            if date_ptr.strftime("%A") != lec["day"]:
                date_ptr += timedelta(days=1)
                continue

            if is_today_national_holiday(sheet, date=date_ptr):
                date_ptr += timedelta(days=1)
                continue

            if is_today_user_holiday(sheet, user_id, date=date_ptr):
                date_ptr += timedelta(days=1)
                continue


            future_lectures += 1
            date_ptr += timedelta(days=1)

    projected_pct = round(
        (present / (total + future_lectures)) * 100, 2
    ) if (total + future_lectures) else 100

    if current_pct < minimum_required:
        risk = "CRITICAL"
        message = "Your attendance is already below the minimum requirement."
    elif projected_pct < minimum_required:
        risk = "HIGH"
        message = "You may fall below the minimum attendance if lectures are missed."
    elif current_pct < minimum_required + 5:
        risk = "BORDERLINE"
        message = "You are close to the minimum attendance threshold."
    else:
        risk = "SAFE"
        message = "Your attendance is safe."

    return {
        "current_pct": current_pct,
        "projected_pct": projected_pct,
        "future_lectures": future_lectures,
        "risk": risk,
        "message": message
    }



# ================== MAIN LOOP ==================

def run():
    sheet = open_spreadsheet(SPREADSHEET_ID)
    print("✅ Notification service started")

    while True:
        try:
            attendance_reminders(sheet)
            timetable_reminders(sheet)
        except Exception as e:
            print("❌ Notification error:", e)

        time.sleep(60)


if __name__ == "__main__":
    run()



