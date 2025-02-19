# frontend/routes/verify.py
import streamlit as st
import requests
from lib.auth import AuthManager
import config

st.set_page_config(**config.DEFAULT_PAGE_CONFIG)

# Initialize authentication
auth = AuthManager(api_url="http://api:8000")


@st.cache_data
def request_verify(key):
    '''simple cached request to avoid triggering the api twice by accident due to streamlit reruns'''
    return requests.get(f"http://api:8000/verify/{key}")


st.title("Email Verification")

# Get verification key from URL parameters
key = st.query_params.get("key")

if not key:
    st.error("No verification key provided")
    st.page_link("routes/home.py", label="Return to Home", use_container_width=True)
    st.stop()

response = request_verify(key)

if response.status_code == 200:
    message = response.json().get("message", "")
    if "already verified" in message.lower():
        st.success("Your email is already verified. Please click Login in the sidebar.")
    else:
        st.success("Email verified successfully! Please click Login in the sidebar.")

else:
    st.error(response.json().get("detail", "Verification failed"))
    st.page_link("routes/home.py", label="Return to Home", use_container_width=True)

