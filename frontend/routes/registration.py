import requests
import streamlit as st
from lib import mail


API_URL = "http://api:8000"
st.title('Organization Registration')

with st.form('registration'):
    col1, col2 = st.columns(2)
    
    with col1:
        org_name = st.text_input('Organization Name')
        org_domain = st.text_input('Organization Domain (optional)')
    
    with col2:
        admin_email = st.text_input('Admin Email')
        password = st.text_input('Password', type='password')
        password_confirm = st.text_input('Confirm Password', type='password')

    submitted = st.form_submit_button('Register')

if submitted:
    if password != password_confirm:
        st.error('Passwords do not match!')
        st.stop()
        
    try:
        response = requests.post(
            f"{API_URL}/admin/register",
            json={
                "email": admin_email,
                "password": password,
                "organization_name": org_name,
                "organization_domain": org_domain
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            verification_url = f"http://localhost:8501/verify?key={data['verification_key']}"
            
            # Send verification email
            mail.send_email(
                to_address=admin_email,
                subject="Verify your Course Platform account",
                body=f"""
                Welcome to Course Platform!
                
                Please click the following link to verify your account:
                {verification_url}
                
                Best regards,
                Course Platform Team
                """
            )
            
            st.success("Registration successful! Please check your email for verification.")
            
        else:
            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


# import uuid
# import random
# import time

# import streamlit as st

# from lib import mail
# from lib import menu


# st.title('Registration')
# menu.navigation()


# @st.cache_data()
# def get_verification_key():
#     return str(uuid.uuid4())


# if 'verification_key' in st.query_params:

#     if st.query_params.verification_key != get_verification_key():
#         st.error('This link is invalid, redirecting in 5 seconds...')
#         time.sleep(5)
#         st.query_params.clear()
#         st.rerun()

#     else:
#         st.success('Registered succesfully! Redirecting to login page in 5 seconds...')
#         time.sleep(5)
#         st.switch_page('pages/login.py')

# else:

#     with st.form('registration'):
#         email = st.text_input('Email')
#         password1 = st.text_input('Password', type='password')
#         password2 = st.text_input('Password Retype', type='password')
#         submitted = st.form_submit_button('Submit')

#     if submitted:

#         if password1 != password2:
#             st.error('Passwords must match!')
#             st.stop()

#         email_body = f'''
#         click here to verify your email: 
#         http://localhost:8501/registration/?verification_key={get_verification_key()}
#         '''

#         mail.send_email(
#             to_address = email,
#             subject = 'verify email',
#             body = email_body
#         )

#         st.success('Email sent!')