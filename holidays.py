from datetime import datetime, date

IST_FORMAT = "%Y-%m-%d"

def today_str():
    return datetime.now().strftime(IST_FORMAT)

def is_today_national_holiday(spreadsheet):
    ws = spreadsheet.worksheet("National_Holidays")
    holidays = ws.get_all_records()

    today = today_str()

    for h in holidays:
        if h["date"] == today:
            return h["title"]
    return None


def is_today_user_holiday(spreadsheet, user_id):
    ws = spreadsheet.worksheet("User_Holidays")
    holidays = ws.get_all_records()

    today = datetime.strptime(today_str(), IST_FORMAT).date()

    for h in holidays:
        if h["user_id"] != user_id:
            continue

        start = datetime.strptime(h["start_date"], IST_FORMAT).date()
        end = datetime.strptime(h["end_date"], IST_FORMAT).date()

        if start <= today <= end:
            return h["title"]
    return None
