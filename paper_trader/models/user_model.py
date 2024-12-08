from dataclasses import dataclass
import sqlite3
import logging
from paper_trader.utils.sql_utils import get_db_connection
from paper_trader.utils.logger import configure_logger
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

logger = logging.getLogger(__name__)
configure_logger(logger)

@dataclass
class User:
    id: int
    username: str
    password: str
    balance: float

def create_user(username: str, password: str, balance: float):
    '''
    Create a new user with a hashed password
    '''
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, balance) VALUES (?, ?, ?)
                ''', (username, hashed_password, balance))
            conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error("user with username %s already exists", username)
        raise ValueError(f"Error creating user: {e}") from e
    

def find_user_by_username(username: str):
    '''
    Find a user by their username
    '''
    try:
        with get_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password, balance FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return User(*user)
            return None
    except sqlite3.Error as e:
        logger.error("Database error finding user by username %s", username)
        raise ValueError(f"Error finding user: {e}") from e

def find_user_by_id(user_id: int):
    '''
    Find a user by their id
    '''
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password, balance FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return User(*user)
            return None
    except sqlite3.Error as e:
        logger.error("Database error finding user by id %s", user_id)
        raise ValueError(f"Error finding user: {e}") from e

def find_user_by_username(old_password:str, new_password: str) -> bool:
    '''
    Find a user by their username
    '''
    connection = sqlite3.connect('db/paper-trader.db')
    cursor = connection.cursor()
    cursor.execute('SELECT id, username, password, balance FROM users WHERE username = ?', (user_id,))
    user = cursor.fetchone()
    connection.close()
    if user:
        return User(*user)
    return None

def update_user_balance(username, new_balance):
    """
    Update a user's balance.
    """
    connection = sqlite3.connect('db/paper-trader.db')
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE users
        SET balance = ?
        WHERE username = ?
    """, (new_balance, username))
    connection.commit()

def delete_user(username):
    """
    Delete a user from the database.
    """
    connection = sqlite3.connect('db/paper-trader.db')
    cursor = connection.cursor()
    cursor.execute("""
        DELETE FROM users
        WHERE username = ?
    """, (username,))
    connection.commit()

def get_all_users():
    """
    Retrieves all users in the database and formats them as a list of dictionaries.

    Returns:
        list[dict]: A list of dictionaries containing user details (ID, username, and balance).
    """
    connection = sqlite3.connect('db/paper-trader.db')
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT id, username, balance FROM users
        """)
        users = cursor.fetchall()
        return [{"id": user[0], "username": user[1], "balance": user[2]} for user in users]
    except sqlite3.Error as e:
        raise ValueError(f"Error retrieving users: {e}")

def update_user_email(user_id, new_email):
    """
    Updates the email address of a user.
    """
    connection = sqlite3.connect('db/paper-trader.db')
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE users
            SET email = ?
            WHERE id = ?
        """, (new_email, user_id))
        if cursor.rowcount == 0:
            raise ValueError("No user found with the specified ID")
        connection.commit()
    except sqlite3.Error as e:
        raise ValueError(f"Error updating user email: {e}")
    
def authenticate_user(username, password):
    """
    Authenticates a user by verifying their username and password.
    
    Returns
        int: The user's ID if authentication is successful.
    """
    connection = sqlite3.connect('db/paper-trader.db')
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT id, password FROM users
            WHERE username = ?
        """, (username,))
        user = cursor.fetchone()
        if user is None:
            raise ValueError("Invalid username or password")
        user_id, hashed_password = user
        if not bcrypt.check_password_hash(hashed_password, password):
            raise ValueError("Invalid username or password")
        return user_id
    except sqlite3.Error as e:
        raise ValueError(f"Error authenticating user: {e}")

def check_password(old_password: str, new_password: str) -> bool:
    '''
    Check if the provided password matches the stored hashed password
    '''
    return bcrypt.check_password_hash(old_password, new_password)

def update_password(user_id: int, new_password: str):
    '''
    Update a user's password
    '''
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database error updating password for user %s", user_id)
        raise ValueError(f"Error updating password: {e}") from e