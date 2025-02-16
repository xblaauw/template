import streamlit as st

st.title('Welcome to Course Platform')

# Add this after the existing "Register Now" button
if st.button("Login"):
    st.switch_page("routes/login.py")

st.markdown("""
### About Our Platform

Our platform helps organizations manage daily learning activities for their teams.

#### How it works:
1. Organization admins register and verify their account
2. Add team members' email addresses
3. Team members receive daily questions via email
4. Track progress and engagement through the admin dashboard

#### Features:
- Easy team member management
- Daily automated questions
- Progress tracking
- Simple one-click responses for team members
""")

if st.button("Register Now"):
    st.switch_page("routes/registration.py")
