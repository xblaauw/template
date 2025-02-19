import datetime as dt

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from sqlalchemy import text

from lib.database import get_db
from lib.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


app = FastAPI()

@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": form_data.username}
    ).fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    expires = dt.datetime.now() + dt.timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": access_token, 
        "expires": expires.isoformat(),
        "token_type": "bearer"
    }

@app.get("/users/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "id": current_user.id,
        "is_verified": current_user.is_verified
    }



from pydantic import BaseModel, EmailStr, field_validator
from lib.auth import get_password_hash
from lib.mail import send_email
import uuid
from sqlalchemy import text

from password_validator import PasswordValidator

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        schema = PasswordValidator()
        schema\
            .min(8)\
            .max(100)\
            .has().uppercase()\
            .has().lowercase()\
            .has().digits()\
            .has().symbols()\
            .no().spaces()

        if not schema.validate(v):
            raise ValueError(
                'Password must be 8-100 characters long, '
                'contain upper and lowercase letters, '
                'numbers, special characters, and no spaces'
            )
        return v

@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    print(f"Registration attempt for email: {user.email}")  # Debug log
    
    # Check if user exists
    existing_user = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": user.email}
    ).fetchone()
    
    if existing_user:
        print(f"User already exists: {user.email}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with verification key
    verification_key = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    try:
        # Insert new user
        result = db.execute(
            text("""
                INSERT INTO users (email, password_hash, verification_key, is_verified)
                VALUES (:email, :password_hash, :verification_key, false)
                RETURNING id, email, verification_key
            """),
            {
                "email": user.email,
                "password_hash": hashed_password,
                "verification_key": verification_key
            }
        )
        new_user = result.fetchone()
        db.commit()
        
        print(f"Created user: {new_user}")  # Debug log
        
        # Send verification email
        verification_url = f"http://localhost:8501/verify?key={verification_key}"
        email_body = f"""
Welcome to the Course Platform!

Please verify your email by clicking the following link:
{verification_url}

If you did not create this account, please ignore this email.
"""
        send_email(
            to_address=user.email,
            subject="Verify your Course Platform account",
            body=email_body
        )
        
        print(f"Sent verification email to: {user.email}")  # Debug log
        return {"message": "Registration successful. Please check your email to verify your account."}
        
    except Exception as e:
        print(f"Error during registration: {str(e)}")  # Debug log
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/verify/{key}")
async def verify_email(key: str, db: Session = Depends(get_db)):
    print(f"Verification attempt with key: {key}")  # Debug log
    
    # First check if this key was ever associated with a user
    user = db.execute(
        text("""
            SELECT * FROM users 
            WHERE verification_key = :key 
            OR (verification_key IS NULL AND is_verified = true)
        """),
        {"key": key}
    ).fetchone()

    print(f"Found user: {user}")  # Debug log

    if not user:
        print(f"No user found for key: {key}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification key"
        )

    # If user is already verified, return success
    if user.is_verified:
        print(f"User already verified: {user.email}")  # Debug log
        return {"message": "Email already verified"}

    try:
        # Update the user to verified status
        result = db.execute(
            text("""
                UPDATE users 
                SET is_verified = true,
                    verification_key = NULL
                WHERE verification_key = :key
                RETURNING id, email
            """),
            {"key": key}
        )
        updated_user = result.fetchone()
        db.commit()
        
        print(f"Successfully verified user: {updated_user}")  # Debug log
        return {"message": "Email verified successfully"}
    except Exception as e:
        print(f"Error during verification: {str(e)}")  # Debug log
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from lib.database import get_db
from lib.auth import get_current_user

@app.get("/credits/summary")
async def get_user_credits(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    credits_info = db.execute(
        text("""
            SELECT 
                available_credits,
                total_transactions,
                last_transaction_date
            FROM user_available_credits 
            WHERE user_id = :user_id
        """),
        {"user_id": current_user.id}
    ).fetchone()
    
    if not credits_info:
        return {
            "available_credits": 0,
            "total_transactions": 0,
            "last_transaction_date": None
        }
    
    return {
        "available_credits": credits_info.available_credits,
        "total_transactions": credits_info.total_transactions,
        "last_transaction_date": credits_info.last_transaction_date.isoformat() if credits_info.last_transaction_date else None
    }



from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from lib.database import get_db
from lib.auth import get_current_user

class ClassCreate(BaseModel):
    name: str

@app.post("/classes")
async def create_class(
    class_data: ClassCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                INSERT INTO classes (owner_id, name)
                VALUES (:owner_id, :name)
                RETURNING id, name, created_at
            """),
            {
                "owner_id": current_user.id,
                "name": class_data.name
            }
        )
        new_class = result.fetchone()
        db.commit()
        
        return {
            "id": new_class.id,
            "name": new_class.name,
            "created_at": new_class.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        # Check if the error is due to duplicate name
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A class with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@app.get("/classes/administered")
async def get_administered_classes(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT id, name, created_at
                FROM classes 
                WHERE owner_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": current_user.id}
        )
        classes = result.fetchall()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "created_at": c.created_at.isoformat()
            }
            for c in classes
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/classes/enrolled")
async def get_enrolled_classes(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT c.id, c.name, s.created_at as enrollment_date
                FROM classes c
                JOIN students s ON c.id = s.class_id
                WHERE s.user_id = :user_id
                ORDER BY s.created_at DESC
            """),
            {"user_id": current_user.id}
        )
        classes = result.fetchall()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "enrolled_at": c.enrollment_date.isoformat()
            }
            for c in classes
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    


@app.get("/classes/{class_id}/students")
async def get_class_students(
    class_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # First verify that the current user is the administrator of this class
    class_check = db.execute(
        text("""
            SELECT id FROM classes 
            WHERE id = :class_id AND owner_id = :user_id
        """),
        {
            "class_id": class_id,
            "user_id": current_user.id
        }
    ).fetchone()
    
    if not class_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the administrator of this class"
        )
    
    # Get student information
    try:
        result = db.execute(
            text("""
                SELECT 
                    u.id,
                    u.email,
                    u.is_verified,
                    s.created_at as enrollment_date
                FROM students s
                JOIN users u ON s.user_id = u.id
                WHERE s.class_id = :class_id
                ORDER BY s.created_at DESC
            """),
            {"class_id": class_id}
        )
        students = result.fetchall()
        
        return [
            {
                "id": student.id,
                "email": student.email,
                "is_verified": student.is_verified,
                "enrolled_at": student.enrollment_date.isoformat()
            }
            for student in students
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )







@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).fetchone()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
