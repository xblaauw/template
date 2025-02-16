import time
import requests
import streamlit as st

API_URL = "http://api:8000"

st.title('Account Verification')

if 'key' in st.query_params:
    verification_key = st.query_params['key']
    
    try:
        response = requests.post(f"{API_URL}/admin/verify/{verification_key}")
        
        if response.status_code == 200:
            st.success("Account verified successfully!")
            st.write("Redirecting to dashboard in 5 seconds...")
            
            # Store admin data in session state
            data = response.json()
            st.session_state.admin_id = data['admin_id']
            st.session_state.org_id = data['organization_id']  # Store organization_id
            st.session_state.is_verified = True
            
            # Clear query params and redirect
            time.sleep(5)
            st.query_params.clear()
            st.switch_page("routes/dashboard.py")
            
        else:
            st.error("Invalid or expired verification link")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.error("No verification key provided")