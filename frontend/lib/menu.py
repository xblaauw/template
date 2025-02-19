import streamlit as st
from lib.auth import AuthManager


auth = AuthManager(api_url="http://api:8000")


def navigation():

    st.header('Menu', divider=True)

    if auth.is_authenticated():
        st.page_link('routes/dashboard.py', label='Dashboard', use_container_width=True)

    else:
        st.page_link('routes/home.py', label='Home', use_container_width=True)
        st.page_link('routes/login.py', label='Login', use_container_width=True)

