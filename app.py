import streamlit as st
from datetime import datetime
from google_sheets import open_spreadsheet
from holidays import is_today_national_holiday, is_today_user_holiday

SPREADSHEET_ID = "1wGnF_bV3pNMx2l3BtwXEfKFdbs3ToYsgxqqgnKBAqgU"

st.set_page_config(page_title="AttendSmart", layout="centered")
st.title("📚 AttendSmart")

spreadsheet = open_spreadsheet(SPREADSHEET_ID)

tab_login, tab_timetable, tab_holidays, tab_attendance, tab_notifications = st.tabs(
    ["🔐 Login", "🗓️ Timetable", "🏖️ Holidays", "📊 Attendance", "🔔 Notifications"]
)

# ---------------- LOGIN TAB ----------------
with tab_login:
    st.subheader("Login")

    name = st.text_input("Name")
    email = st.text_input("Email")

    def get_or_create_user(name, email):
        users_ws = spreadsheet.worksheet("Users")
        users = users_ws.get_all_records()

        for user in users:
            if user["email"] == email:
                return user["user_id"]

        user_id = len(users) + 1
        users_ws.append_row([
            user_id,
            name,
            email,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        return user_id

    if st.button("Login"):
        if not name or not email:
            st.error("Please enter name and email")
        else:
            user_id = get_or_create_user(name, email)
            st.session_state["user_id"] = user_id
            st.success(f"Logged in successfully! User ID: {user_id}")


# ---------------- HOLIDAY TAB ----------------
with tab_holidays:
    if "user_id" not in st.session_state:
        st.warning("Please login first")
    else:
        st.subheader("🏖️ Add Holiday / Leave")

        start_date = st.date_input("Start date")
        end_date = st.date_input("End date", min_value=start_date)
        title = st.text_input("Reason / Title")
        category = st.selectbox("Category", ["personal", "institutional"], key="add_holiday_category")

        if st.button("Add Holiday"):
            if not title:
                st.error("Please add a title")
            else:
                ws = spreadsheet.worksheet("User_Holidays")
                ws.append_row([
                    st.session_state["user_id"],
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    title,
                    category,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
                st.success("Holiday added 🎉")

        st.subheader("📋 Your Holidays")
        ws = spreadsheet.worksheet("User_Holidays")
        all_rows = ws.get_all_records()
        user_id = str(st.session_state["user_id"])

        user_holidays = []
        for idx, row in enumerate(all_rows, start=2):  # start=2 because row 1 = header
            if str(row["user_id"]) == user_id:
                row["_row"] = idx
                user_holidays.append(row)

        st.table(user_holidays)

        st.subheader("✏️ Edit Holiday")

        if user_holidays:
            selected = st.selectbox(
                "Select holiday to edit",
                user_holidays,
                format_func=lambda x: f"{x['start_date']} → {x['end_date']} | {x['title']}"
            )

            new_start = st.date_input(
                "New start date",
                value=datetime.fromisoformat(selected["start_date"]),
                key="edit_holiday_start"
            )

            new_end = st.date_input(
                "New end date",
                value=datetime.fromisoformat(selected["end_date"]),
                key="edit_holiday_end"
            )

            new_title = st.text_input(
                "New title",
                value=selected["title"],
                key="edit_holiday_title"
            )

            new_category = st.selectbox(
                "Category",
                ["personal", "institutional"],
                index=0 if selected["category"] == "personal" else 1,
                key="edit_holiday_category"
            )


            if st.button("Update Holiday"):
                ws.update(f"B{selected['_row']}:E{selected['_row']}", [[
                    new_start.strftime("%Y-%m-%d"),
                    new_end.strftime("%Y-%m-%d"),
                    new_title,
                    new_category
                ]])
                st.success("Holiday updated ✅")
                st.experimental_rerun()

        st.subheader("❌ Delete Holiday")

        if user_holidays:
            del_item = st.selectbox(
                "Select holiday to delete",
                user_holidays,
                format_func=lambda x: f"{x['start_date']} → {x['end_date']} | {x['title']}",
                key="delete_holiday"
            )

            if st.button("Delete Holiday"):
                ws.delete_rows(del_item["_row"])
                st.success("Holiday deleted 🗑️")
                st.experimental_rerun()



# ---------------- TIMETABLE TAB ----------------
with tab_timetable:
    if "user_id" not in st.session_state:
        st.warning("Please login first")
    else:
        # Holiday block (TODAY)
        national = is_today_national_holiday(spreadsheet)
        if national:
            st.info(f"🎉 Today is a National Holiday: **{national}**")
            st.stop()

        user_holiday = is_today_user_holiday(spreadsheet, st.session_state["user_id"])
        if user_holiday:
            st.info(f"🏖️ Today is your holiday: **{user_holiday}**")
            st.stop()

        st.subheader("🗓️ Add Lecture")

        day = st.selectbox(
            "Day",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], key="add_lecture_day"
        )
        subject = st.text_input("Subject")
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")

        if st.button("Add Lecture"):
            timetable_ws = spreadsheet.worksheet("Timetable")
            timetable_ws.append_row([
                st.session_state["user_id"],
                day,
                subject,
                start_time.strftime("%H:%M"),
                end_time.strftime("%H:%M")
            ])
            st.success("Lecture added ✅")

        st.subheader("📋 Your Lectures")
        timetable_ws = spreadsheet.worksheet("Timetable")
        rows = timetable_ws.get_all_records()

        user_lectures = []
        for idx, row in enumerate(rows, start=2):
            if str(row["user_id"]) == user_id:
                row["_row"] = idx
                user_lectures.append(row)

        st.table(user_lectures)

        st.subheader("✏️ Edit Lecture")

        if user_lectures:
            lec = st.selectbox(
                "Select lecture",
                user_lectures,
                format_func=lambda x: f"{x['day']} | {x['subject']} ({x['start_time']}-{x['end_time']})"
            )

            new_day = st.selectbox(
                "Day",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                index=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"].index(lec["day"]),
                key="edit_lecture_day"
            )

            new_subject = st.text_input(
                "Subject",
                value=lec["subject"],
                key="edit_lecture_subject"
            )

            new_start = st.time_input(
                "Start",
                datetime.strptime(lec["start_time"], "%H:%M").time(),
                key="edit_lecture_start"
            )

            new_end = st.time_input(
                "End",
                datetime.strptime(lec["end_time"], "%H:%M").time(),
                key="edit_lecture_end"
            )


            if st.button("Update Lecture"):
                timetable_ws.update(f"B{lec['_row']}:E{lec['_row']}", [[
                    new_day,
                    new_subject,
                    new_start.strftime("%H:%M"),
                    new_end.strftime("%H:%M")
                ]])
                st.success("Lecture updated ✅")
                st.experimental_rerun()

        st.subheader("❌ Delete Lecture")

        if user_lectures:
            del_lec = st.selectbox(
                "Select lecture to delete",
                user_lectures,
                format_func=lambda x: f"{x['day']} | {x['subject']}",
                key="delete_lecture"
            )

            if st.button("Delete Lecture"):
                timetable_ws.delete_rows(del_lec["_row"])
                st.success("Lecture deleted 🗑️")
                st.experimental_rerun()


# ---------------- ATTENDANCE TAB ----------------
with tab_attendance:
    if "user_id" not in st.session_state:
        st.warning("Please login first")
    else:
        st.subheader("📊 Today’s Attendance")

        today = datetime.now().strftime("%Y-%m-%d")
        today_day = datetime.now().strftime("%A")
        user_id = str(st.session_state["user_id"])

        timetable_ws = spreadsheet.worksheet("Timetable")
        attendance_ws = spreadsheet.worksheet("Attendance")

        lectures = timetable_ws.get_all_records()
        attendance = attendance_ws.get_all_records()

        # Today's lectures
        today_lectures = [
            l for l in lectures
            if str(l["user_id"]) == user_id and l["day"] == today_day
        ]

        if not today_lectures:
            st.info("No lectures scheduled for today 🎉")
        else:
            for lec in today_lectures:
                already_marked = next(
                    (a for a in attendance
                     if str(a["user_id"]) == user_id
                     and a["date"] == today
                     and a["subject"] == lec["subject"]
                     and a["start_time"] == lec["start_time"]),
                    None
                )

                st.markdown(f"### 📘 {lec['subject']} ({lec['start_time']} – {lec['end_time']})")

                if already_marked:
                    st.success(f"Marked as **{already_marked['status']}**")
                else:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("✅ Yes", key=f"yes_{lec['subject']}_{lec['start_time']}"):
                            attendance_ws.append_row([
                                user_id,
                                today,
                                today_day,
                                lec["subject"],
                                lec["start_time"],
                                lec["end_time"],
                                "Yes",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                            st.rerun()

                    with col2:
                        if st.button("❌ No", key=f"no_{lec['subject']}_{lec['start_time']}"):
                            attendance_ws.append_row([
                                user_id,
                                today,
                                today_day,
                                lec["subject"],
                                lec["start_time"],
                                lec["end_time"],
                                "No",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                            st.rerun()

                    with col3:
                        if st.button("🚫 Off", key=f"off_{lec['subject']}_{lec['start_time']}"):
                            attendance_ws.append_row([
                                user_id,
                                today,
                                today_day,
                                lec["subject"],
                                lec["start_time"],
                                lec["end_time"],
                                "Off",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                            st.rerun()

# ---------------- NOTIFICATIONS TAB ----------------
with tab_notifications:
    st.subheader("🔔 Notification Preferences")

    ws = spreadsheet.worksheet("Notification_Settings")
    data = ws.get_all_records()

    existing = next(
        (r for r in data if str(r["user_id"]) == str(st.session_state["user_id"])),
        None
    )

    telegram = st.checkbox(
        "Telegram Notifications",
        value=(existing and existing["telegram"] == "yes"),
        key="notif_telegram"
    )

    email = st.checkbox(
        "Email Notifications",
        value=(existing and existing["email"] == "yes"),
        key="notif_email"
    )

    in_app = st.checkbox(
        "In-App Notifications",
        value=(existing and existing["in_app"] == "yes"),
        key="notif_inapp"
    )

    email_id = st.text_input(
        "Email ID",
        value=(existing["email_id"] if existing else ""),
        disabled=not email
    )

    if st.button("Save Notification Settings"):
        if existing:
            row_index = data.index(existing) + 2
            ws.update(f"B{row_index}:G{row_index}", [[
                "yes" if telegram else "no",
                "yes" if email else "no",
                "yes" if in_app else "no",
                existing["telegram_chat_id"],
                email_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]])
        else:
            ws.append_row([
                st.session_state["user_id"],
                "yes" if telegram else "no",
                "yes" if email else "no",
                "yes" if in_app else "no",
                "",
                email_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

        st.success("Notification preferences saved ✅")

