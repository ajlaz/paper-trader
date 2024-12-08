import pytest
from contextlib import contextmanager
import re
import sqlite3
from unittest.mock import patch
from paper_trader.models.user_model import create_user, find_user_by_username, find_user_by_id, update_user_balance, delete_user, get_all_users, update_user_email, authenticate_user, check_password, update_password
from paper_trader.models.user_model import User

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

@pytest.fixture
def user_model():
    """Fixture to provide a new instance of UserModel for each test."""
    return User()

@pytest.fixture
def sample_user():
    """Sample user data for testing purposes."""
    return {
        "id": 1,
        "username": "test_user",
        "email": "test_user@example.com",
        "password": "securepassword"
    }

@pytest.fixture
def another_sample_user():
    """Another sample user for testing."""
    return {
        "id": 2,
        "username": "another_user",
        "email": "another_user@example.com",
        "password": "anothersecurepassword"
    }

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
    mock_cursor.execute.return_value.fetchone.return_value = ("user", "hashed_password", 1000.0)

    user = find_user_by_username("user")

    expected_query = normalize_whitespace("""
        SELECT username, password, balance
        FROM users
        WHERE username = ?
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the correct parameter was used
    assert mock_cursor.execute.call_args[0][1] == ("user",), "Expected query parameter to be ('user',)."

    # Assert the function returned the correct user data
    assert user.username == "user", "Expected username to match 'user'."
    assert user.password == "hashed_password", "Expected password to match 'hashed_password'."
    assert user.balance == 1000.0, "Expected balance to match 1000.0."


def test_get_user_by_username_not_found(mock_cursor):
    '''Test retrieving a user that does not exist'''

    # Simulate the database returning no rows
    mock_cursor.execute.return_value.fetchone.return_value = None

    with pytest.raises(ValueError, match="User not found"):
        find_user_by_username("nonexistent_user")


def test_update_user_balance(mock_cursor):
    '''Test updating a user's balance'''

    # Call the function to update the user's balance
    update_user_balance("user", 1200.0)

    expected_query = normalize_whitespace("""
        UPDATE users
        SET balance = ?
        WHERE username = ?
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the correct parameters were used
    assert mock_cursor.execute.call_args[0][1] == (1200.0, "user"), "Expected query parameters to be (1200.0, 'user')."


def test_delete_user(mock_cursor):
    '''Test deleting a user'''

    # Call the function to delete a user
    delete_user("user")

    expected_query = normalize_whitespace("""
        DELETE FROM users
        WHERE username = ?
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the correct parameter was used
    assert mock_cursor.execute.call_args[0][1] == ("user",), "Expected query parameter to be ('user',)."


def test_get_all_users(mock_cursor):
    '''Test retrieving all users'''

    # Simulate the database returning multiple rows
    mock_cursor.execute.return_value.fetchall.return_value = [
        ("user1", "hashed_password1", 1000.0),
        ("user2", "hashed_password2", 2000.0)
    ]

    users = get_all_users()

    expected_query = normalize_whitespace("""
        SELECT username, password, balance
        FROM users
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert the returned users match the database rows
    assert len(users) == 2, "Expected to retrieve 2 users."
    assert users[0].username == "user1", "Expected first user to be 'user1'."
    assert users[1].balance == 2000.0, "Expected second user's balance to be 2000.0."

def test_update_user_email(mock_cursor, mock_bcrypt):
    """Test updating a user's email."""
    update_user_email(user_id=1, new_email="new_email@example.com")

    expected_query = normalize_whitespace("""
        UPDATE users
        SET email = ?
        WHERE id = ?
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "SQL query for updating email is incorrect."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("new_email@example.com", 1)
    assert actual_arguments == expected_arguments, f"Arguments for updating email are incorrect. Expected {expected_arguments}, got {actual_arguments}."


def test_authenticate_user(mock_cursor, mock_bcrypt):
    """Test authenticating a user with valid credentials."""
    mock_cursor.fetchone.return_value = (1, "hashed_password")

    mock_bcrypt.check_password_hash.return_value = True

    user_id = authenticate_user(username="user", password="password")
    assert user_id == 1, "Failed to authenticate user with valid credentials."

def test_authenticate_user_invalid_password(mock_cursor, mock_bcrypt):
    """Test authenticating a user with an invalid password."""
    mock_cursor.fetchone.return_value = (1, "hashed_password")

    mock_bcrypt.check_password_hash.return_value = False

    with pytest.raises(ValueError, match="Invalid username or password"):
        authenticate_user(username="user", password="wrong_password")

##################################################
#
#   Edge Case Test Cases
#
##################################################

def test_get_nonexistent_user_by_id(mock_cursor, mock_bcrypt):
    """Test getting a user by ID when the user does not exist."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="User not found"):
        find_user_by_id(999)


def test_update_email_for_nonexistent_user(mock_cursor, mock_bcrypt):
    """Test updating the email of a nonexistent user."""
    mock_cursor.execute.return_value = None
    mock_cursor.rowcount = 0

    with pytest.raises(ValueError, match="No user found with the specified ID"):
        update_user_email(user_id=999, new_email="nonexistent@example.com")

def test_delete_nonexistent_user(mock_cursor, mock_bcrypt):
    """Test deleting a nonexistent user."""
    mock_cursor.execute.return_value = None
    mock_cursor.rowcount = 0

    with pytest.raises(ValueError, match="No user found with the specified ID"):
        delete_user(user_id=999)

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
    mock_bcrypt.generate_password_hash.return_value = hashed_password

    # Act
    update_password(user_id, new_password)

    # Assert
    mock_bcrypt.generate_password_hash.assert_called_once_with(new_password)
    mock_cursor.execute.assert_called_once_with(
        'UPDATE users SET password = ? WHERE id = ?',
        (hashed_password, user_id)
    )
    assert mock_cursor.execute.call_count == 1, "Password update query was not executed exactly once."

    

    