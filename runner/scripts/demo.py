from lib.config import settings, setup_logger
from lib.database import Base, get_db, get_df, check_connection
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd


logger = setup_logger()


logger.info("Starting demo script")

if not check_connection():
    logger.error("Failed to connect to database - exiting script!")
    exit()

logger.info("Successfully connected to database")


# Using SQLAlchemy ORM with get_df and get_db
try:
    logger.info('Database class keys available through SQLAlchemy ORM:')
    logger.info(Base.classes.keys())

    Measurements = Base.classes.measurements
    
    with get_db() as session:
        results = session.query(Measurements).order_by(Measurements.timestamp.desc()).all()
        
        # Use get_df to convert results to DataFrame
        logger.info('Retrieving measurements from db')
        df = get_df(results)
        logger.info(f"Retrieved {len(df)} rows using ORM")
        
        logger.info('computing mean stats')
        stats = df.filter(['temperature', 'humidity', 'pressure']).mean().to_dict()
        
        logger.info("Measurement statistics calculated", extra=stats)
        logger.info(stats)
        
except Exception as e:
    logger.error(f"Error in ORM query: {str(e)}")
    raise
