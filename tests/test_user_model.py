import pytest
import sqlite3
from unittest.mock import patch
from paper_trader.models.user_model import create_table, create_user, find_user_by_username, check_password, update_password

@pytest.fixture(scope="module")
def db_connection():
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 10000.0
        )
    ''')
    connection.commit()
    yield connection
    connection.close()

def test_create_table(db_connection):
    create_table()
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'users'")
    assert cursor.fetchone() is not None

@patch('bcrypt.generate_password_hash', return_value=b'hash123')
def test_create_user(mock_bcrypt, db_connection):
    create_user('testuser', 'password123', 5000.0)
    cursor = db_connection.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
    user = cursor.fetchone()
    assert user is not None
    assert user[1] == 'testuser'
    assert user[3] == 5000.0

def test_find_user_by_username(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", 
                   ('findme', 'hash123', 10000.0))
    db_connection.commit()
    user = find_user_by_username('findme')
    assert user is not None
    assert user.username == 'findme'

@patch('bcrypt.check_password_hash', return_value=True)
def test_check_password(mock_bcrypt):
    result = check_password('hash123', 'password123')
    assert result is True

@patch('bcrypt.generate_password_hash', return_value=b'newhash123')
def test_update_password(mock_bcrypt, db_connection):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", 
                   ('updateuser', 'hash123', 10000.0))
    user_id = cursor.lastrowid
    db_connection.commit()
    update_password(user_id, 'newpassword123')
    cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
    updated_password = cursor.fetchone()[0]
    assert updated_password == 'newhash123'