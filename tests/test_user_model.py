import pytest
from contextlib import contextmanager
import re
import sqlite3
from unittest.mock import patch
from paper_trader.models.user_model import create_user, find_user_by_username, find_user_by_id, check_password, update_password

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("paper_trader.models.user_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

@pytest.fixture
def mock_bcrypt(mocker):
    return mocker.patch("flask_bcrypt.Bcrypt.generate_password_hash", return_value=b'password')

######################################################
#
#    Add Users
#
######################################################

def test_create_user(mock_cursor, mock_bcrypt):
    '''Test creating a new user'''
    
    #Call the function to create a new user
    create_user(username="user", password="password", balance=1000.0)
    
    expected_query = normalize_whitespace("""
        INSERT INTO users (username, password, balance)
        VALUES (?, ?, ?)
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("user", "password", 1000.0)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_user_duplicate_username(mock_cursor, mock_bcrypt):
    '''Test creating a new user with a duplicate username'''
    
    #Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: users.username")
    
    #expect that the correct error is raised
    with pytest.raises(ValueError, match="Error creating user: UNIQUE constraint failed: users.username"):
        create_user(username="user", password="password", balance=1000.0)