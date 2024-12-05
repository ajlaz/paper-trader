from dataclasses import dataclass
import sqlite3
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

@dataclass
class User:
    id: int
    username: str
    password: str
    balance: float

    def create_table():
        '''
        Create the users table if it doesn't already exist
        '''
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT UNIQUE NOT NULL,
                       password TEXT NOT NULL,
                       balance REAL DEFAULT 10000.0
            )
        '''
        )
        connection.commit()
        connection.close()

    def create_user(username: str, password: str):
        '''
        Create a new user with a hashed password
        '''
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password) VALUES (?, ?)
                ''', (username, hashed_password))
            connection.commit()
        except sqlite3.IntegrityError as e:
            connection.close()
            raise ValueError(f"Error creating user: {e}")
        connection.close()

    def find_user_by_username(username: str):
        '''
        Find a user by their username
        '''
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT id, username, password, balance FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        connection.close()
        if user:
            return User(*user)
        return None
    
    def check_password(self, password: str) -> bool:
        '''
        Check if the provided password matches the stored hashed password
        '''
        return bcrypt.check_password_hash(self.password, password)

    