import streamlit as st

pages = [
    st.Page('routes/home.py', title='Home'),
    st.Page('routes/registration.py', title='Registration'),
    st.Page('routes/login.py', title='Login'),  # Add this line
    st.Page('routes/verify.py', title='Verify Account'),
    st.Page('routes/dashboard.py', title='Dashboard'),
]

pg = st.navigation(pages, position='hidden', expanded=True)
pg.run()
