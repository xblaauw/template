# frontend/lib/auth.py
import streamlit as st
import requests
import time
import datetime as dt
from streamlit_cookies_controller import CookieController
from typing import Optional, Dict, Any


class AuthManager:
    def __init__(self, api_url: str, token_cookie_name: str = "auth_token"):
        self.api_url = api_url
        self.token_cookie_name = token_cookie_name
        self.cookie_controller = CookieController()
        
    def get_token(self) -> Optional[str]:
        """Get the authentication token from cookies."""
        return self.cookie_controller.get(self.token_cookie_name)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return bool(self.get_token())
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Attempt to login user and return result."""
        response = requests.post(
            url=f"{self.api_url}/token",
            data={"username": email, "password": password}
        )
        result = response.json()
        
        if 'access_token' in result:
            token = result['access_token']
            expires = dt.datetime.fromisoformat(result['expires'])
            self.cookie_controller.set(
                name=self.token_cookie_name,
                value=token,
                expires=expires,
            )
            time.sleep(1)  # Give the cookie some time to appear
            return {"success": True, "message": "Logged in successfully!"}
            
        elif 'detail' in result:
            return {"success": False, "message": result['detail']}
        
        return {"success": False, "message": "Unknown error"}
    
    def logout(self) -> None:
        """Logout user by removing the auth token."""
        self.cookie_controller.remove(self.token_cookie_name)
        time.sleep(1)  # Give the cookie some time to cleanup
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        token = self.get_token()
        if not token:
            return None
            
        response = requests.get(
            url=f"{self.api_url}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json() if response.status_code == 200 else None

def create_login_ui(auth: AuthManager) -> None:
    """Create login UI components."""
    st.header('Login', divider=True)
    email    = st.text_input('Email')
    password = st.text_input('Password', type='password')
    
    if st.button('login', type='primary', use_container_width=True):
        result = auth.login(email, password)
        if result["success"]:
            st.switch_page('routes/dashboard.py')
        else:
            st.error(result["message"])

def create_logout_ui(auth: AuthManager) -> None:
    """Create logout UI components."""
    if st.button('Logout', type='primary', use_container_width=True):
        st.warning('Logging you out...')
        auth.logout()
        st.switch_page('routes/home.py')
