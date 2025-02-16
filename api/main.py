import os
import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime, timezone
from fastapi.logger import logger


app = FastAPI()

# Database connection
def get_db():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        cursor_factory=RealDictCursor
    )

# Pydantic models
class OrganizationCreate(BaseModel):
    name: str
    domain: Optional[str] = None

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    organization_name: str
    organization_domain: Optional[str] = None

class ManagedUserCreate(BaseModel):
    emails: List[EmailStr]

class QuestionCreate(BaseModel):
    question_text: str
    options: List[dict]  # [{text: str, is_correct: bool}]
    question_set_id: int

class QuestionResponse(BaseModel):
    access_token: uuid.UUID
    selected_option_id: int

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/admin/register")
async def register_admin(admin: AdminCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            # Create organization
            cur.execute(
                "INSERT INTO organizations (name, domain) VALUES (%s, %s) RETURNING id",
                (admin.organization_name, admin.organization_domain)
            )
            org_id = cur.fetchone()['id']
            
            # Create admin user
            verification_key = uuid.uuid4()
            password_hash = hash_password(admin.password)
            
            cur.execute(
                """
                INSERT INTO admin_users (organization_id, email, password_hash, verification_key) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
                """,
                (org_id, admin.email, password_hash, str(verification_key))  # Convert UUID to string here
            )
            admin_id = cur.fetchone()['id']
            
            # Initialize subscription credits
            cur.execute(
                "INSERT INTO subscription_credits (organization_id, credits_remaining) VALUES (%s, %s)",
                (org_id, 0)  # Start with 0 credits
            )
            
            conn.commit()
    
    return {
        "admin_id": admin_id,
        "organization_id": org_id,
        "verification_key": verification_key  # This is fine as FastAPI will handle UUID serialization
    }

@app.post("/admin/verify/{verification_key}")
async def verify_admin(verification_key: uuid.UUID):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT au.id as admin_id, au.organization_id 
                FROM admin_users au
                WHERE au.verification_key = %s
                """,
                (str(verification_key),)
            )
            result = cur.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Invalid verification key")
            
            # Clear verification key and set verified
            cur.execute(
                """
                UPDATE admin_users 
                SET is_verified = TRUE, verification_key = NULL 
                WHERE id = %s
                """,
                (result['admin_id'],)
            )
            conn.commit()
    
    return {
        "status": "verified", 
        "admin_id": result['admin_id'],
        "organization_id": result['organization_id']
    }

# Managed Users Management
@app.post("/organization/{org_id}/users")
async def add_managed_users(org_id: int, users: ManagedUserCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            # First verify organization exists
            cur.execute("SELECT id FROM organizations WHERE id = %s", (org_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Organization not found")
            
            # Add users
            added_users = []
            for email in users.emails:
                try:
                    cur.execute(
                        """
                        INSERT INTO managed_users (organization_id, email) 
                        VALUES (%s, %s) 
                        ON CONFLICT (organization_id, email) DO NOTHING 
                        RETURNING id
                        """,
                        (org_id, email)
                    )
                    result = cur.fetchone()
                    if result:
                        added_users.append(email)
                except psycopg2.Error:
                    continue
            
            conn.commit()
    
    return {"added_users": added_users}

# Question Assignment and Response
@app.post("/assignments/create")
async def create_daily_assignments():
    """
    Create daily assignments for all active managed users.
    This would typically be called by a scheduled task.
    """
    today = date.today()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get all active managed users
            cur.execute(
                """
                SELECT id FROM managed_users 
                WHERE is_active = TRUE
                """
            )
            users = cur.fetchall()
            
            # Get a question for each user
            # (In a real implementation, you'd want more sophisticated question selection)
            cur.execute("SELECT id FROM questions LIMIT 1")
            question = cur.fetchone()
            if not question:
                raise HTTPException(status_code=404, detail="No questions available")
            
            # Create assignments
            for user in users:
                access_token = uuid.uuid4()
                cur.execute(
                    """
                    INSERT INTO daily_assignments 
                    (managed_user_id, question_id, access_token, assigned_for_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (managed_user_id, question_id, assigned_for_date) DO NOTHING
                    """,
                    (user['id'], question['id'], access_token, today)
                )
            
            conn.commit()
    
    return {"status": "assignments created"}

@app.get("/question/{access_token}")
async def get_question(access_token: uuid.UUID):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    q.question_text,
                    ao.id as option_id,
                    ao.option_text
                FROM daily_assignments da
                JOIN questions q ON da.question_id = q.id
                JOIN answer_options ao ON q.id = ao.question_id
                WHERE da.access_token = %s
                AND da.is_answered = FALSE
                """,
                (str(access_token),)  # Convert UUID to string
            )
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(status_code=404, detail="Invalid or expired access token")
            
            # Format response
            question_text = results['question_text']
            options = [
                {"id": r['option_id'], "text": r['option_text']}
                for r in results
            ]
    
    return {
        "question_text": question_text,
        "options": options
    }

@app.post("/question/respond")
async def submit_response(response: QuestionResponse):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id 
                FROM daily_assignments 
                WHERE access_token = %s 
                AND is_answered = FALSE
                """,
                (str(response.access_token),)  # Convert UUID to string
            )
            assignment = cur.fetchone()
            
            if not assignment:
                raise HTTPException(
                    status_code=404, 
                    detail="Invalid access token or question already answered"
                )
            
            # Record response
            cur.execute(
                """
                INSERT INTO user_responses (daily_assignment_id, selected_option_id)
                VALUES (%s, %s)
                """,
                (assignment['id'], response.selected_option_id)
            )
            
            # Mark assignment as answered
            cur.execute(
                """
                UPDATE daily_assignments 
                SET is_answered = TRUE 
                WHERE id = %s
                """,
                (assignment['id'],)
            )
            
            conn.commit()
    
    return {"status": "response recorded"}

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

# Question Set Management

class QuestionSetCreate(BaseModel):
    name: str
    description: Optional[str] = None

@app.post("/question-sets")
async def create_question_set(question_set: QuestionSetCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO question_sets (name, description) VALUES (%s, %s) RETURNING id, name, description",
                (question_set.name, question_set.description)
            )
            new_set = cur.fetchone()
            conn.commit()
    return new_set

@app.get("/question-sets")
async def get_question_sets():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM question_sets ORDER BY created_at DESC")
            return cur.fetchall()

@app.get("/question-sets/{set_id}/questions")
async def get_questions(set_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    q.id, 
                    q.question_text,
                    json_agg(
                        json_build_object(
                            'id', ao.id,
                            'text', ao.option_text,
                            'is_correct', ao.is_correct
                        )
                    ) as options
                FROM questions q
                LEFT JOIN answer_options ao ON q.id = ao.question_id
                WHERE q.question_set_id = %s
                GROUP BY q.id
                ORDER BY q.created_at DESC
                """,
                (set_id,)
            )
            return cur.fetchall()
        
# Question functionality

class QuestionCreate(BaseModel):
    question_text: str
    options: List[dict]  # each dict should have 'text' and 'is_correct' keys
    question_set_id: int

@app.post("/questions")
async def create_question(question: QuestionCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            # First create the question
            cur.execute(
                """
                INSERT INTO questions (question_set_id, question_text)
                VALUES (%s, %s)
                RETURNING id
                """,
                (question.question_set_id, question.question_text)
            )
            question_id = cur.fetchone()['id']
            
            # Then create all the options
            for option in question.options:
                cur.execute(
                    """
                    INSERT INTO answer_options (question_id, option_text, is_correct)
                    VALUES (%s, %s, %s)
                    """,
                    (question_id, option['text'], option['is_correct'])
                )
            
            conn.commit()
            
            return {"id": question_id, "status": "created"}
        
# login functionality

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/admin/login")
async def login_admin(login_data: LoginRequest):
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get admin user
            cur.execute(
                """
                SELECT id, organization_id, password_hash, is_verified 
                FROM admin_users 
                WHERE email = %s
                """,
                (login_data.email,)
            )
            user = cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Verify password
            if hash_password(login_data.password) != user['password_hash']:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if user is verified
            if not user['is_verified']:
                raise HTTPException(status_code=403, detail="Account not verified")
            
            return {
                "admin_id": user['id'],
                "organization_id": user['organization_id']
            }


# enroll users

from typing import List

class EnrollmentRequest(BaseModel):
    user_ids: List[int]
    question_set_id: int

@app.post("/enroll-users")
async def enroll_users(enrollment: EnrollmentRequest):
    with get_db() as conn:
        with conn.cursor() as cur:
            # First get all questions from the question set
            cur.execute(
                "SELECT id FROM questions WHERE question_set_id = %s",
                (enrollment.question_set_id,)
            )
            questions = cur.fetchall()
            
            if not questions:
                raise HTTPException(status_code=404, detail="No questions found in question set")
            
            # Create assignments for each user and question
            assignments_created = 0
            for user_id in enrollment.user_ids:
                for question in questions:
                    access_token = uuid.uuid4()
                    try:
                        cur.execute(
                            """
                            INSERT INTO daily_assignments 
                            (managed_user_id, question_id, access_token, assigned_for_date)
                            VALUES (%s, %s, %s, CURRENT_DATE)
                            ON CONFLICT (managed_user_id, question_id, assigned_for_date) 
                            DO NOTHING
                            RETURNING id
                            """,
                            (user_id, question['id'], str(access_token))
                        )
                        if cur.fetchone():
                            assignments_created += 1
                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Error creating assignment: {str(e)}"
                        )
            
            conn.commit()
            
            return {
                "status": "success",
                "assignments_created": assignments_created,
                "users_enrolled": len(enrollment.user_ids)
            }

# org users list

@app.get("/organization/{org_id}/users")
async def get_organization_users(org_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    mu.id,
                    mu.email,
                    mu.is_active,
                    mu.created_at,
                    json_agg(
                        json_build_object(
                            'question_set_name', qs.name,
                            'assigned_date', da.assigned_for_date,
                            'is_answered', da.is_answered
                        )
                    ) FILTER (WHERE qs.id IS NOT NULL) as enrollments
                FROM managed_users mu
                LEFT JOIN daily_assignments da ON mu.id = da.managed_user_id
                LEFT JOIN questions q ON da.question_id = q.id
                LEFT JOIN question_sets qs ON q.question_set_id = qs.id
                WHERE mu.organization_id = %s
                GROUP BY mu.id, mu.email, mu.is_active, mu.created_at
                ORDER BY mu.created_at DESC
                """,
                (org_id,)
            )
            users = cur.fetchall()
            
            return users

# create daily assignments
import psycopg2.extensions
import uuid
from lib import mail

# Register UUID type adapter
def adapt_uuid(uuid):
    return psycopg2.extensions.QuotedString(str(uuid))

psycopg2.extensions.register_adapter(uuid.UUID, adapt_uuid)

class DailyAssignmentCreate(BaseModel):
    organization_id: int
    question_set_id: int

@app.post("/assignments/create")
async def create_daily_assignments(assignment: DailyAssignmentCreate):
    """
    Create daily assignments for all active managed users in an organization
    for a specific question set and send emails.
    """
    today = date.today()
    
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Get all active managed users with their email addresses
                cur.execute(
                    """
                    SELECT id, email FROM managed_users 
                    WHERE organization_id = %s AND is_active = TRUE
                    """,
                    (assignment.organization_id,)
                )
                users = cur.fetchall()
                
                if not users:
                    raise HTTPException(
                        status_code=404, 
                        detail={
                            "message": "No active users found",
                            "organization_id": assignment.organization_id
                        }
                    )
                
                # Get questions from the specified question set
                cur.execute(
                    """
                    SELECT id FROM questions 
                    WHERE question_set_id = %s
                    """,
                    (assignment.question_set_id,)
                )
                questions = cur.fetchall()
                
                if not questions:
                    raise HTTPException(
                        status_code=404, 
                        detail={
                            "message": "No questions found in question set",
                            "question_set_id": assignment.question_set_id
                        }
                    )
                
                # Get question set name
                cur.execute(
                    "SELECT name FROM question_sets WHERE id = %s",
                    (assignment.question_set_id,)
                )
                question_set = cur.fetchone()
                
                if not question_set:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "message": "Question set not found",
                            "question_set_id": assignment.question_set_id
                        }
                    )
                
                # Create assignments and send emails
                assignments_created = 0
                emails_sent = 0
                errors = []
                
                for user in users:
                    user_assignments = []
                    for question in questions:
                        access_token = uuid.uuid4()
                        try:
                            cur.execute(
                                """
                                INSERT INTO daily_assignments 
                                (managed_user_id, question_id, access_token, assigned_for_date)
                                VALUES (%s, %s, %s::uuid, %s)
                                ON CONFLICT (managed_user_id, question_id, assigned_for_date) 
                                DO NOTHING
                                RETURNING id
                                """,
                                (user['id'], question['id'], str(access_token), today)
                            )
                            if cur.fetchone():
                                assignments_created += 1
                                question_link = f"http://localhost:8501/question?token={access_token}"
                                user_assignments.append(question_link)
                        except Exception as e:
                            errors.append(f"Error creating assignment for user {user['id']}: {str(e)}")
                            continue
                    
                    # Send email if assignments were created for this user
                    if user_assignments:
                        try:
                            email_body = f"""
                            Hello!

                            You have new questions to answer for {question_set['name']}.
                            
                            Click the links below to answer each question:
                            
                            {chr(10).join(f'- {link}' for link in user_assignments)}
                            
                            Best regards,
                            Course Platform Team
                            """
                            
                            logger.info(f"Attempting to send email to {user['email']}")
                            logger.info(f"Email body:\n{email_body}")
                            
                            mail.send_email(
                                to_address=user['email'],
                                subject=f"Daily Questions: {question_set['name']}",
                                body=email_body
                            )
                            emails_sent += 1
                            logger.info(f"Successfully sent email to {user['email']}")
                        except Exception as e:
                            error_msg = f"Error sending email to {user['email']}: {str(e)}"
                            logger.info(error_msg)
                            errors.append(error_msg)
                
                conn.commit()
        
        return {
            "status": "assignments created and emails sent",
            "assignments_created": assignments_created,
            "emails_sent": emails_sent,
            "users_processed": len(users),
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


