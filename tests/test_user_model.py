import pytest
from contextlib import contextmanager
import re
import sqlite3
from unittest.mock import patch, Mock
from paper_trader.models.user_model import create_user, find_user_by_username, find_user_by_id, update_user_balance, check_password, update_password

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
    mock_bcrypt = mocker.patch("paper_trader.models.user_model.bcrypt")
    mock_bcrypt.generate_password_hash.return_value = b'password'
    mock_bcrypt.check_password_hash.return_value = True
    return mock_bcrypt

######################################################
#
#    User Management Test Cases
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

def test_get_user_by_username(mock_cursor):
    '''Test retrieving a user by username'''

    # Simulate the database returning a user row
    mock_cursor.fetchone.return_value = (1, "user", "hashed_password", 1000.0)

    user = find_user_by_username("user")

    expected_query = normalize_whitespace("""
        SELECT id, username, password, balance
        FROM users
        WHERE username = ?
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the returned user is correct
    assert user.username == "user"
    assert user.password == "hashed_password"
    assert user.balance == 1000.0


def test_get_user_by_username_not_found(mock_cursor):
    '''Test retrieving a user that does not exist'''

    # Simulate the database returning no rows
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="User with username nonexistent_user not found"):
        find_user_by_username("nonexistent_user")

def test_get_user_by_username_database_error(mock_cursor):
    '''Test retrieving a user when a database error occurs'''

    # Simulate the database raising an error
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")

    with pytest.raises(sqlite3.Error, match="Database error"):
        find_user_by_username("user")
        
def test_get_user_by_id(mock_cursor):
    '''Test retrieving a user by ID'''

    # Simulate the database returning a user row
    mock_cursor.fetchone.return_value = (1, "user", "hashed_password", 1000.0)

    user = find_user_by_id(1)

    expected_query = normalize_whitespace("""
        SELECT id, username, password, balance
        FROM users
        WHERE id = ?
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the returned user is correct
    assert user.username == "user"
    assert user.password == "hashed_password"
    assert user.balance == 1000.0

def test_get_user_by_id_not_found(mock_cursor):
    '''Test retrieving a user by ID that does not exist'''

    # Simulate the database returning no rows
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="User with ID 2 not found"):
        find_user_by_id(2)

def test_get_user_by_id_database_error(mock_cursor):
    '''Test retrieving a user by ID when a database error occurs'''

    # Simulate the database raising an error
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")

    with pytest.raises(ValueError, match="Error finding user: Database error"):
        find_user_by_id(1)


def test_update_user_balance(mock_cursor):
    '''Test updating a user's balance'''

    # Call the function to update the user's balance
    update_user_balance(1, 1200.0)

    expected_query = normalize_whitespace("""
        UPDATE users
        SET balance = ?
        WHERE id = ?
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the correct parameters were used
    assert mock_cursor.execute.call_args[0][1] == (1200.0, 1), "Expected query parameters to be (1200.0, 'user')."
    
def test_update_user_balance_error(mock_cursor):
    '''Test updating a user's balance when an error occurs'''

    # Simulate that the database will raise an error
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")

    with pytest.raises(sqlite3.Error, match="Database error"):
        update_user_balance("user", 1200.0)




##################################################
#
#   Password Management Test Cases
#
##################################################

def test_check_password(mock_bcrypt):
    """Test checking a password with the stored hashed password."""

    # Arrange
    hashed_password = "hashed_password"
    provided_password = "plain_password"

    # Mock bcrypt to simulate successful password match
    mock_bcrypt.check_password_hash.return_value = True

    # Act
    result = check_password(hashed_password, provided_password)

    # Assert
    mock_bcrypt.check_password_hash.assert_called_once_with(hashed_password, provided_password)
    assert result is True, "Password check failed when it should have succeeded."

def test_check_password_failure(mock_bcrypt):
    """Test checking a password when the stored hash does not match."""

    # Arrange
    hashed_password = "hashed_password"
    provided_password = "wrong_password"

    # Mock bcrypt to simulate failed password match
    mock_bcrypt.check_password_hash.return_value = False

    # Act
    result = check_password(hashed_password, provided_password)

    # Assert
    mock_bcrypt.check_password_hash.assert_called_once_with(hashed_password, provided_password)
    assert result is False, "Password check succeeded when it should have failed."

def test_update_password(mock_cursor, mock_bcrypt):
    """Test updating a user's password."""

    # Arrange
    user_id = 1
    new_password = "new_password"
    hashed_password = "hashed_password"

    # Mock bcrypt to generate the hashed password
    mock_bcrypt.generate_password_hash.return_value = b'hashed_password'

    # Act
    update_password(user_id, new_password)

    # Assert
    mock_bcrypt.generate_password_hash.assert_called_once_with(new_password)
    mock_cursor.execute.assert_called_once_with(
        'UPDATE users SET password = ? WHERE id = ?',
        (hashed_password, user_id)
    )
    assert mock_cursor.execute.call_count == 1, "Password update query was not executed exactly once."