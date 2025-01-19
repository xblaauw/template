from lib.config import settings, setup_log
from lib.database import Base, get_db, get_df, check_connection
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd


log = setup_log()


log.info("Starting demo script")

if not check_connection():
    log.error("Failed to connect to database - exiting script!")
    exit()

log.info("Successfully connected to database")


# Using SQLAlchemy ORM with get_df and get_db
log.info('Database class keys available through SQLAlchemy ORM:')
log.info(Base.classes.keys())

Measurements = Base.classes.measurements

with get_db() as session:
    results = session.query(Measurements).order_by(Measurements.timestamp.desc()).all()
    
    # Use get_df to convert results to DataFrame
    log.info('Retrieving measurements from db')
    df = get_df(results)
    log.info(f"Retrieved {len(df)} rows using ORM")
    
    log.info('computing mean stats')
    stats = df.filter(['temperature', 'humidity', 'pressure']).mean().to_dict()
    
    log.info("Measurement statistics calculated", extra=stats)
    log.info(stats)
