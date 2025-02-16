import requests
import streamlit as st

API_URL = "http://api:8000"

st.title('Login')

# Initialize session state
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

if st.session_state.is_logged_in:
    st.success("You are logged in!")
    if st.button("Go to Dashboard"):
        st.switch_page("routes/dashboard.py")
else:
    with st.form('login_form'):
        email = st.text_input('Email')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')

        if submitted:
            try:
                response = requests.post(
                    f"{API_URL}/admin/login",
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Store in session state
                    st.session_state.admin_id = data['admin_id']
                    st.session_state.org_id = data['organization_id']
                    st.session_state.is_logged_in = True
                    st.session_state.is_verified = True  # Since we checked in the API
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    error_msg = response.json().get('detail', 'Login failed')
                    st.error(f"Login failed: {error_msg}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
