import streamlit as st


def navigation():
    c1, c2, c3 = st.columns(3)

    c1.page_link('routes/home.py', label='Home', use_container_width=True)
    c2.page_link('routes/registration.py', label = 'Registration', use_container_width=True)

