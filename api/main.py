# api/main.py
import os
import psycopg2
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

# Database connection settings
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    return conn

# Example data model
class ExampleData(BaseModel):
    id: int
    name: str

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}"
        )

# Example endpoint (no authentication required)
@app.get("/example")
async def example_endpoint():
    return {"message": "Hello, World!"}

# Example of using the data model
@app.post("/example")
async def create_example(data: ExampleData):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO example_table (name) VALUES (%s)", (data.name,))
        conn.commit()
        return {"message": "Data created successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        cur.close()
        conn.close()