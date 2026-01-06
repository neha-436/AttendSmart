# from datetime import datetime, date

# IST_FORMAT = "%Y-%m-%d"

# def today_str():
#     return datetime.now().strftime(IST_FORMAT)

# def is_national_holiday(sheet, date):
#     """
#     date: datetime.date or YYYY-MM-DD string
#     """
#     if not isinstance(date, str):
#         date = date.strftime("%Y-%m-%d")

#     holidays = sheet.worksheet("National_Holidays").get_all_records()

#     for h in holidays:
#         if h["date"] == date:
#             return h["title"]

#     return None



# def is_today_user_holiday(spreadsheet, user_id):
#     ws = spreadsheet.worksheet("User_Holidays")
#     holidays = ws.get_all_records()

#     today = datetime.strptime(today_str(), IST_FORMAT).date()

#     for h in holidays:
#         if h["user_id"] != user_id:
#             continue

#         start = datetime.strptime(h["start_date"], IST_FORMAT).date()
#         end = datetime.strptime(h["end_date"], IST_FORMAT).date()

#         if start <= today <= end:
#             return h["title"]
#     return None


from datetime import datetime, date
from sheet_cache import load_user_holidays, load_national_holidays

IST_FORMAT = "%Y-%m-%d"


# ---------- Helpers ----------

def normalize_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, IST_FORMAT).date()
    return d


def today_date():
    return datetime.now().date()


# ---------- NATIONAL HOLIDAYS ----------

def is_national_holiday(spreadsheet, check_date):
    """
    check_date: datetime.date or YYYY-MM-DD
    """
    check_date = normalize_date(check_date)

    holidays = load_national_holidays(spreadsheet)

    for h in holidays:
        h_date = normalize_date(h["date"])
        if h_date == check_date:
            return h["title"]

    return None


def is_today_national_holiday(spreadsheet):
    return is_national_holiday(spreadsheet, today_date())


# ---------- USER HOLIDAYS ----------

def is_user_holiday(spreadsheet, user_id, check_date):
    """
    check_date: datetime.date or YYYY-MM-DD
    """
    check_date = normalize_date(check_date)

    holidays = load_user_holidays(spreadsheet)

    for h in holidays:
        if str(h["user_id"]) != str(user_id):
            continue

        start = normalize_date(h["start_date"])
        end = normalize_date(h["end_date"])

        if start <= check_date <= end:
            return h["title"]

    return None


def is_today_user_holiday(spreadsheet, user_id):
    return is_user_holiday(spreadsheet, user_id, today_date())

