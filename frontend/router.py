import streamlit as st

from lib.menu import navigation


pages = [
    st.Page('routes/home.py', title='Home'),
    st.Page('routes/verify.py', title='Verify', url_path='verify'),
    st.Page('routes/dashboard.py', title='Dashboard', url_path='dashboard'),
    st.Page('routes/login.py', title='Login', url_path='login'),
]

pg = st.navigation(pages, position='hidden', expanded=True)
pg.run()

