import requests
import streamlit as st
import pandas as pd

API_URL = "http://api:8000"

# Initialize session state
if 'is_verified' not in st.session_state:
    st.session_state.is_verified = False
if 'admin_id' not in st.session_state:
    st.session_state.admin_id = None
if 'org_id' not in st.session_state:
    st.session_state.org_id = None

# Check if user is verified
if not st.session_state.is_verified:
    st.error("Please verify your account first")
    st.switch_page("routes/home.py")

st.title('Organization Dashboard')

with st.sidebar:
    st.title("Navigation")
    page = st.radio(
        "Go to",
        ["Manage Team", "Question Sets", "Send Daily Questions", "Reports"]  # Added new option
    )

# Page: Manage Team
if page == "Manage Team":
    st.header("Team Members")
    
    # Display current team members
    try:
        response = requests.get(
            f"{API_URL}/organization/{st.session_state.org_id}/users"
        )
        
        if response.status_code == 200:
            users_data = response.json()
            df = pd.DataFrame(users_data)
            
            if not df.empty:
                # Prepare data for display
                df = df.rename(columns={
                    'email': 'Email',
                    'is_active': 'Active',
                    'created_at': 'Joined Date',
                    'enrollments': 'Enrolled In'
                })
                
                if 'Joined Date' in df.columns:
                    df['Joined Date'] = pd.to_datetime(df['Joined Date']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Format enrollments as a readable string
                def format_enrollments(enrollments):
                    if not enrollments or enrollments is None:
                        return "Not enrolled"
                    # Convert string 'null' to empty list if necessary
                    if isinstance(enrollments, str) and enrollments.lower() == 'null':
                        return "Not enrolled"
                    # Get unique question sets
                    unique_sets = {e['question_set_name'] for e in enrollments}
                    return ", ".join(unique_sets)
                
                df['Enrolled In'] = df['Enrolled In'].apply(format_enrollments)
                
                # Add selection checkboxes
                df['select'] = False
                selected_users = st.data_editor(
                    df,
                    column_config={
                        "select": st.column_config.CheckboxColumn(
                            "Select",
                            default=False,
                        ),
                        "Enrolled In": st.column_config.TextColumn(
                            "Enrolled In",
                            help="Question sets the user is enrolled in"
                        )
                    },
                    hide_index=True
                )
                
                # Get selected user IDs
                selected_user_ids = selected_users[selected_users['select']]['id'].tolist()
                
                # Show enrollment options if users are selected
                if selected_user_ids:
                    st.subheader("Enroll Selected Users")
                    
                    # Get available question sets
                    question_sets_response = requests.get(f"{API_URL}/question-sets")
                    if question_sets_response.status_code == 200:
                        question_sets = question_sets_response.json()
                        
                        selected_set = st.selectbox(
                            "Select Question Set",
                            options=question_sets,
                            format_func=lambda x: x['name']
                        )
                        
                        if st.button("Enroll Users"):
                            try:
                                # Make API call to enroll users
                                enroll_response = requests.post(
                                    f"{API_URL}/enroll-users",
                                    json={
                                        "user_ids": selected_user_ids,
                                        "question_set_id": selected_set['id']
                                    }
                                )
                                
                                if enroll_response.status_code == 200:
                                    st.success(f"Successfully enrolled {len(selected_user_ids)} users in {selected_set['name']}")
                                    st.rerun()  # Refresh to show updated enrollments
                                else:
                                    st.error("Failed to enroll users: " + enroll_response.json().get('detail', 'Unknown error'))
                            except Exception as e:
                                st.error(f"Error enrolling users: {str(e)}")
            else:
                st.info("No team members found.")
                
            # Add new team members form
            st.subheader("Add Team Members")
            with st.form("add_team_members"):
                emails = st.text_area(
                    "Email Addresses",
                    help="Enter one email address per line"
                )
                submitted = st.form_submit_button("Add Team Members")
            
            if submitted:
                email_list = [email.strip() for email in emails.split('\n') if email.strip()]
                try:
                    response = requests.post(
                        f"{API_URL}/organization/{st.session_state.org_id}/users",
                        json={"emails": email_list}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Added {len(data['added_users'])} team members successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    
    except Exception as e:
        st.error(f"Failed to load team members: {str(e)}")

# Page: Question Sets
elif page == "Question Sets":
    st.header("Question Sets")
    
    # Create new question set
    with st.expander("Create New Question Set"):
        with st.form("new_question_set"):
            set_name = st.text_input("Question Set Name")
            set_description = st.text_area("Description")
            submit_set = st.form_submit_button("Create Question Set")
            
        if submit_set and set_name:
            try:
                response = requests.post(
                    f"{API_URL}/question-sets",
                    json={
                        "name": set_name,
                        "description": set_description
                    }
                )
                if response.status_code == 200:
                    st.success("Question set created successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to create question set: {str(e)}")

    # View and manage existing question sets
    try:
        response = requests.get(f"{API_URL}/question-sets")
        if response.status_code == 200:
            question_sets = response.json()
            
            if not question_sets:
                st.info("No question sets found. Create your first one!")
            else:
                selected_set = st.selectbox(
                    "Select Question Set",
                    options=question_sets,
                    format_func=lambda x: x['name']
                )
                
                if selected_set:
                    st.subheader(f"Questions in: {selected_set['name']}")
                    st.write(selected_set['description'])
                    
                    # Add new question
                    with st.expander("Add New Question"):
                        with st.form("new_question"):
                            question_text = st.text_area("Question")
                            
                            st.write("Options (mark correct answer)")
                            options = []
                            for i in range(4):
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    option_text = st.text_input(f"Option {i+1}", key=f"opt_{i}")
                                with col2:
                                    is_correct = st.checkbox("Correct", key=f"correct_{i}")
                                if option_text:
                                    options.append({"text": option_text, "is_correct": is_correct})
                            
                            submit_question = st.form_submit_button("Add Question")
                        
                        if submit_question and question_text and options:
                            try:
                                response = requests.post(
                                    f"{API_URL}/questions",
                                    json={
                                        "question_text": question_text,
                                        "options": options,
                                        "question_set_id": selected_set['id']
                                    }
                                )
                                if response.status_code == 200:
                                    st.success("Question added successfully!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Failed to add question: {str(e)}")
                    
                    # Display existing questions
                    try:
                        response = requests.get(f"{API_URL}/question-sets/{selected_set['id']}/questions")
                        if response.status_code == 200:
                            questions = response.json()
                            for q in questions:
                                with st.expander(q['question_text']):
                                    for opt in q['options']:
                                        correct = "✓" if opt['is_correct'] else " "
                                        st.write(f"[{correct}] {opt['text']}")
                    except Exception as e:
                        st.error(f"Failed to load questions: {str(e)}")
                        
    except Exception as e:
        st.error(f"Failed to load question sets: {str(e)}")


elif page == "Send Daily Questions":
    st.header("Send Daily Questions")
    
    # Get available question sets
    try:
        response = requests.get(f"{API_URL}/question-sets")
        if response.status_code == 200:
            question_sets = response.json()
            
            if not question_sets:
                st.warning("No question sets available. Please create a question set first.")
            else:
                selected_set = st.selectbox(
                    "Select Question Set",
                    options=question_sets,
                    format_func=lambda x: x['name']
                )
                
                if st.button("Send Daily Questions"):
                    with st.spinner("Sending questions..."):
                        try:
                            # Call the API to create assignments
                            response = requests.post(
                                f"{API_URL}/assignments/create",
                                json={
                                    "organization_id": st.session_state.org_id,
                                    "question_set_id": selected_set['id']
                                }
                            )
                            
                            # Always show the raw response for debugging
                            st.code(f"Response Status: {response.status_code}")
                            st.code(f"Response Body: {response.text}")
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"""
                                Questions sent successfully!
                                - Assignments created: {result.get('assignments_created', 0)}
                                - Emails sent: {result.get('emails_sent', 0)}
                                - Users processed: {result.get('users_processed', 0)}
                                """)
                            else:
                                st.error("Failed to send questions")
                                st.error(f"Error details: {response.text}")
                                
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
                            st.error("Full error details:")
                            st.exception(e)
                            
    except Exception as e:
        st.error(f"Failed to load question sets: {str(e)}")
        st.error("Full error details:")
        st.exception(e)


# Page: Reports
elif page == "Reports":
    st.header("Reports")
    st.info("Reporting functionality coming soon")

# Debug information
with st.sidebar:
    st.divider()
    st.write("Debug Info:")
    st.write(f"Admin ID: {st.session_state.admin_id}")
    st.write(f"Org ID: {st.session_state.org_id}")