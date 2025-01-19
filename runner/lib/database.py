import logging
import pandas as pd

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.engine import URL

from contextlib import contextmanager

from lib.config import settings


# Read schema from environment variables
SCHEMA = settings.POSTGRES_SCHEMA

logger = logging.getLogger(__name__)

# Create URL object for SQLAlchemy
def create_db_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg2",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB
    )

# Create SQLAlchemy engine
engine = create_engine(create_db_url(), echo=settings.DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use metadata to specify schema
metadata = MetaData(schema=SCHEMA)

# Reflect all tables from the specified schema
metadata.reflect(bind=engine)

# Create base class that automatically maps to the tables
Base = automap_base(metadata=metadata)
Base.prepare(engine, reflect=True)

# Get all table names that were found
table_names = metadata.tables.keys()


@contextmanager
def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def check_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def get_df(results):
    """
    Convert SQLAlchemy query results into a Pandas DataFrame.

    Args:
        results (list): A list of SQLAlchemy ORM objects.

    Returns:
        pd.DataFrame: A DataFrame representation of the query results.
                      Includes correct column names and dtypes even if results are empty.
    """
    if not results:
        # If results are empty, infer schema from the mapped table class
        if hasattr(results, "_entities") and len(results._entities) > 0:
            model = results._entities[0].class_
            if hasattr(model, "__table__"):
                columns = model.__table__.columns.keys()
                dtypes = {col.name: str(col.type) for col in model.__table__.columns}
                return pd.DataFrame(columns=columns).astype(dtypes)
            else:
                raise ValueError("The model does not have a __table__ attribute to infer schema.")
        raise ValueError("Unable to infer schema from the results.")

    # Get column names from the first result
    if hasattr(results[0], '__table__'):
        columns = results[0].__table__.columns.keys()
    else:
        columns = [attr for attr in dir(results[0]) if not attr.startswith('_') and not callable(getattr(results[0], attr))]

    # Convert the list of objects into a list of dictionaries
    data = [
        {col: getattr(row, col) for col in columns}
        for row in results
    ]

    # Create and return a DataFrame
    return pd.DataFrame(data)
