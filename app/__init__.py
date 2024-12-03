from flask import Flask
import psycopg2

# Initialize the Flask app
app = Flask(__name__)

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    dbname="project_zero",
    user="postgres",
    password="",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Create a users table (if not already created)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    );
""")
conn.commit()

# Import routes (ensure circular imports are avoided)
from app.routes import *
