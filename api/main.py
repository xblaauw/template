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


#### API endpoints here



#### Final endpoint for healthcheck
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

