-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS {{POSTGRES_SCHEMA}};

-- Set the schema for the session
SET search_path TO {{POSTGRES_SCHEMA}};

-- Create demo table
CREATE TABLE IF NOT EXISTS demo.measurements (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sensor_id VARCHAR(50) NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    pressure DECIMAL(7,2)
);

-- Insert demo data
INSERT INTO demo.measurements (sensor_id, temperature, humidity, pressure) VALUES
    ('sensor_001', 22.5, 45.7, 1013.25),
    ('sensor_001', 23.1, 44.3, 1013.15),
    ('sensor_002', 21.8, 48.2, 1012.95),
    ('sensor_002', 21.9, 47.8, 1013.05),
    ('sensor_003', 23.5, 43.1, 1013.35);