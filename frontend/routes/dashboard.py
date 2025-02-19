import streamlit as st
import requests
import requests
import datetime as dt

from lib.auth import AuthManager, create_logout_ui
from lib.menu import navigation
import config

st.set_page_config(**config.DEFAULT_PAGE_CONFIG)


with st.sidebar:
    navigation()

st.title('Dashboard')

# Initialize authentication
api_baseurl = "http://api:8000"
auth = AuthManager(api_url=api_baseurl)
auth_token = auth.get_token()

# Handle unauthenticated users
if not auth.is_authenticated():
    st.error('Please login using the link in the sidebar')
    st.stop()

# Get user info
user_info = auth.get_user_info()

# User info and logout in sidebar
with st.sidebar:
    st.header('Logged in', divider=True)
    st.text(user_info["email"])
    create_logout_ui(auth)

st.header('Course Credits', divider=True)

def get_credit_data():

    # Set up headers with the bearer token
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    # Make the request
    response = requests.get(
        url     = f"{api_baseurl}/credits/summary",
        headers = headers
    )
    if response.status_code == 200:
        result = response.json()
        result['last_transaction_date'] = dt.datetime.fromisoformat(result['last_transaction_date'])
        return result

    else:
        raise ValueError(response.content)


credit_data = get_credit_data()
credit_metrics = st.columns(len(credit_data))
i = 0
for k, v in credit_data.items():
    if not type(v) in (int, float, str, None):
        v = str(v.date())

    credit_metrics[i].metric(
        label = k,
        value = v,
    )
    i += 1


st.header('Create Class', divider = True)

# Create form for class creation
with st.form("create_class_form"):
    class_name = st.text_input("Class Name")
    submit_button = st.form_submit_button("Create Class")

    if submit_button:
        try:
            # Set up headers with the bearer token
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            # Make the request
            response = requests.post(
                url=f"{api_baseurl}/classes",
                headers=headers,
                json={"name": class_name}
            )
            
            if response.status_code == 200:
                st.success(f"Class '{class_name}' created successfully!")
                # Optional: Display the created class details
                class_data = response.json()
                st.json(class_data)
            else:
                # Display error message from API
                error_detail = response.json().get('detail', 'Unknown error occurred')
                st.error(f"Failed to create class: {error_detail}")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


st.header('My Classes', divider=True)
# Function to fetch administered classes
def get_administered_classes():
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        url=f"{api_baseurl}/classes/administered",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(response.content)

# Function to fetch students for a specific class
def get_class_students(class_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        url=f"{api_baseurl}/classes/{class_id}/students",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(response.content)
    
# Display administered classes
st.subheader("Classes I Administer")
try:
    admin_classes = get_administered_classes()
    if not admin_classes:
        st.info("You don't administer any classes yet.")
    else:
        for class_info in admin_classes:
            with st.expander(class_info["name"]):
                st.write(f"Class ID: {class_info['id']}")
                st.write(f"Created: {dt.datetime.fromisoformat(class_info['created_at']).date()}")
                
                # Add student information
                st.divider()
                st.write("Students:")
                try:
                    students = get_class_students(class_info['id'])
                    if not students:
                        st.info("No students enrolled yet.")
                    else:
                        # Create a DataFrame for better display
                        import pandas as pd
                        df = pd.DataFrame(students)
                        df['enrolled_at'] = pd.to_datetime(df['enrolled_at']).dt.date
                        st.dataframe(
                            df.rename(columns={
                                'email': 'Email',
                                'is_verified': 'Verified',
                                'enrolled_at': 'Enrolled Date'
                            }),
                            hide_index=True
                        )
                except Exception as e:
                    st.error(f"Error loading student data: {str(e)}")

except Exception as e:
    st.error(f"Error loading administered classes: {str(e)}")


# Function to fetch enrolled classes
def get_enrolled_classes():
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        url=f"{api_baseurl}/classes/enrolled",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(response.content)

st.subheader("Classes I'm Enrolled In")
try:
    enrolled_classes = get_enrolled_classes()
    if not enrolled_classes:
        st.info("You're not enrolled in any classes yet.")
    else:
        for class_info in enrolled_classes:
            with st.expander(class_info["name"]):
                st.write(f"Class ID: {class_info['id']}")
                st.write(f"Enrolled: {dt.datetime.fromisoformat(class_info['enrolled_at']).date()}")
except Exception as e:
    st.error(f"Error loading enrolled classes: {str(e)}")
