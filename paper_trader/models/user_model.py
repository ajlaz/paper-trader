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

def create_user(username: str, password: str, balance: float) -> None:
    '''
    Create a new user with a hashed password
    
    Args:
        username (str): The username of the user
        password (str): The password of the user
        balance (float): The initial balance of the user
    
    Raises:
        ValueError: If the user already exists
        sqlite3.Error: If there is a database error
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
    except sqlite3.Error as e:
        logger.error("Database error creating user with username %s", username)
        raise e
    

def find_user_by_username(username: str) -> User:
    '''
    Find a user by their username
    
    Args:
        username (str): The username of the user
    
    Returns:
        User: The User object corresponding to the username
    
    Raises:
        ValueError: If the user is not found
        sqlite3.Error: If there is a database error
    '''
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password, balance FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                return User(*user)
            else:
                logger.info("User with username %s not found", username)
                raise ValueError(f"User with username {username} not found")
    except sqlite3.Error as e:
        logger.error("Database error finding user by username %s", username)
        raise e

def find_user_by_id(user_id: int) -> User:
    '''
    Find a user by their id
    
    Args:
        user_id (int): The ID of the user
    
    Returns:
        User: The User object corresponding to the ID
    
    Raises:
        ValueError: If the user is not found
        sqlite3.Error: If there is a database error
    '''
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password, balance FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                return User(*user)
            else:
                logger.info("User with ID %s not found", user_id)
                raise ValueError(f"User with ID {user_id} not found")
    except sqlite3.Error as e:
        logger.error("Database error finding user by id %s", user_id)
        raise ValueError(f"Error finding user: {e}") from e


def update_user_balance(username, new_balance) -> None:
    """
    Update a user's balance.
    
    Args:
        username (str): The username of the user
        new_balance (float): The new balance of the user
    
    Raises:
        sqlite3.Error: If there is a database error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET balance = ?
                WHERE id = ?
            """, (new_balance, username))
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database error updating balance for user %s", username)
        raise e

def check_password(old_password: str, new_password: str) -> bool:
    '''
    Check if the provided password matches the stored hashed password
    
    Args:
        old_password (str): The stored hashed password
        new_password (str): The new password to check
    
    Returns:
        bool: True if the passwords match, False otherwise
    '''
    return bcrypt.check_password_hash(old_password, new_password)

def update_password(user_id: int, new_password: str):
    '''
    Update a user's password
    
    Args:
        user_id (int): The ID of the user
        new_password (str): The new password to set
    
    Raises:
        sqlite3.Error: If there is a database error
    '''
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database error updating password for user %s", user_id)
        raise e