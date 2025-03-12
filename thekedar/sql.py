import sqlite3

# Database Connection Function
def get_db_connection():
    conn = sqlite3.connect('majdur.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if not exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT CHECK(role IN ('worker', 'employer')) NOT NULL,
                        location TEXT,
                        skills TEXT,
                        experience INTEGER,
                        company_name TEXT,
                        profile_picture TEXT
                    )''')

    # Jobs Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        location TEXT NOT NULL,
                        salary INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        employer TEXT NOT NULL)''')

    # Messages Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        receiver TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()

# Run this file separately to create database tables
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")