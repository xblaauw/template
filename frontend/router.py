import streamlit as st

pages = [
    st.Page('routes/home.py', title='Home', url_path='home'),
]

pg = st.navigation(pages, position='hidden', expanded=True)
pg.run()
