import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ✅ Cache Google Sheets client (VERY IMPORTANT)
@st.cache_resource(show_spinner=False)
def get_gsheet_client():
    creds = Credentials.from_service_account_file(
        "attendsmart-482611-d4e53c2dabec.json",
        scopes=SCOPES
    )
    return gspread.authorize(creds)


# ✅ Cache spreadsheet open
@st.cache_resource(show_spinner=False)
def open_spreadsheet(spreadsheet_id):
    client = get_gsheet_client()
    return client.open_by_key(spreadsheet_id)


def get_or_create_user_sheets(spreadsheet, email):
    safe_email = email.replace("@", "_").replace(".", "_")

    attendance_name = f"{safe_email}_attendance"
    timetable_name = f"{safe_email}_timetable"

    worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}

    # Attendance sheet
    if attendance_name not in worksheets:
        attendance_ws = spreadsheet.add_worksheet(
            title=attendance_name, rows=100, cols=5
        )
        attendance_ws.update(
            range_name="A1",
            values=[["Subject", "Attended", "Conducted"]]
        )
    else:
        attendance_ws = worksheets[attendance_name]

    # Timetable sheet
    if timetable_name not in worksheets:
        timetable_ws = spreadsheet.add_worksheet(
            title=timetable_name, rows=100, cols=6
        )
        timetable_ws.update(
            range_name="A1",
            values=[["Day", "Subject", "Start Time", "End Time"]]
        )
    else:
        timetable_ws = worksheets[timetable_name]

    return attendance_ws, timetable_ws
