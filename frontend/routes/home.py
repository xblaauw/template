# frontend/routes/home.py
import streamlit as st

import requests

from lib.auth import AuthManager
from lib.menu import navigation
import config

st.set_page_config(**config.DEFAULT_PAGE_CONFIG)


with st.sidebar:
    navigation()


# Initialize authentication
auth = AuthManager(api_url="http://api:8000")

if auth.is_authenticated():
    st.switch_page('routes/dashboard.py')


st.title("Course Platform")


st.markdown("""
### Transform Your Organization's Learning Journey

Welcome to Course Platform, your all-in-one solution for corporate training and certification.

#### Key Features:
- **Streamlined Learning Management**: Easily manage courses and track progress
- **Custom Organization Control**: Full control over your organization's learning path
- **Certification System**: Built-in certification with automatic verification
- **Credit-Based Enrollment**: Flexible course enrollment using credits
""")

# Registration Form
st.header("Create Your Account", divider=True)

with st.form("register_form"):
    email = st.text_input("Email")
    email_errors = st.empty()

    password = st.text_input("Password", type="password")
    password_errors = st.empty()

    confirm_password = st.text_input("Confirm Password", type="password")
    confirm_password_errors = st.empty()
    
    submitted = st.form_submit_button("Sign Up", use_container_width=True)
    
    if submitted:

        if password != confirm_password:
            confirm_password_errors.error("Passwords do not match")
        
        try:
            response = requests.post(
                url  = "http://api:8000/register",
                json = {"email": email, "password": password}
            )
        
            if response.status_code == 200:
                st.success("Registration successful! Please check your email to verify your account.")

            elif response.status_code == 400:
                if 'detail' in response.json():
                    detail = response.json()['detail']
                    if detail == 'Email already registered':
                        st.warning(f'{detail}, please login using the link in the sidebar')
            
            elif response.status_code == 422:
                result = response.json()
                if 'detail' in result:
                    for detail in result['detail']:
                        if detail['loc'][1] == 'email':
                            email_errors.error(detail['msg'])
                        if detail['loc'][1] == 'password':
                            password_errors.error(detail['msg'])
            else:
                st.error(response.json().get("detail", "Registration failed"))
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")



