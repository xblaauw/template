import streamlit as st
from lib.auth import AuthManager, create_login_ui
from lib.menu import navigation
import config

st.set_page_config(**config.DEFAULT_PAGE_CONFIG)


with st.sidebar:
    navigation()


# Initialize authentication
auth = AuthManager(api_url="http://api:8000")

# Handle unauthenticated users
if not auth.is_authenticated():
    create_login_ui(auth)
    st.stop()

# Send already logged-in users to the dashboard
else:
    st.switch_page('routes/dashboard.py')

