import streamlit as st

@st.cache_data(ttl=300)
def load_user_holidays(_spreadsheet):
    return _spreadsheet.worksheet("User_Holidays").get_all_records()

@st.cache_data(ttl=300)
def load_national_holidays(_spreadsheet):
    return _spreadsheet.worksheet("National_Holidays").get_all_records()
