from contextlib import contextmanager
import re
import sqlite3

import pytest

from paper_trader.models.user_stock_model import (
    buy_stock,
    sell_stock,
    get_portfolio,
    UserStock,
)
from paper_trader.models.user_model import User

######################################################
#
#    Fixtures and Utilities
#
######################################################


def normalize_whitespace(sql_query: str) -> str:
    """Utility function to normalize whitespace in SQL queries for comparison."""
    return re.sub(r"\s+", " ", sql_query).strip()


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

    mocker.patch(
        "paper_trader.models.user_model.get_db_connection", mock_get_db_connection
    )
    mocker.patch(
        "paper_trader.models.user_stock_model.get_db_connection", mock_get_db_connection
    )

    return mock_cursor  # Return the mock cursor so we can set expectations per test

@pytest.fixture
def mock_quote(mocker):
    mock_quote = mocker.patch("paper_trader.models.user_stock_model.quote_stock_by_symbol")
    mock_quote.return_value = {"05. price": "150.0"}
    return mock_quote
    


######################################################
#
#    Buy Stock Tests
#
######################################################


def test_buy_new_stock(mock_cursor, mock_quote):
    """Test buying a new stock for a user."""
    # Mock stock price from API
    mock_cursor.fetchone.side_effect = [
        (1, "test_user", "hashed_password", 1000.0),  # User data
        None,  # No existing stock
    ]

    
    new_balance = buy_stock(user_id=1, symbol="GOOG", quantity=2)

    # Check SQL queries
    expected_user_query = normalize_whitespace(
        "SELECT id, username, password, balance FROM users WHERE id = ?"
    )
    actual_user_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[0][0][0]
    )
    assert actual_user_query == expected_user_query, "User SELECT query mismatch."

    expected_stock_query = normalize_whitespace(
        "INSERT INTO user_stocks (user_id, symbol, bought_price, quantity) VALUES (?, ?, ?, ?)"
    )
    actual_stock_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[2][0][0]
    )
    assert actual_stock_query == expected_stock_query, "Stock INSERT query mismatch."

    # Assert parameters for stock insertion
    expected_args = (1, "GOOG", 150.0, 2)
    actual_args = mock_cursor.execute.call_args_list[2][0][1]
    assert actual_args == expected_args, f"Expected {expected_args}, got {actual_args}"

    # Assert final balance update
    expected_balance_update_query = normalize_whitespace(
        "UPDATE users SET balance = ? WHERE id = ?"
    )
    actual_balance_update_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[3][0][0]
    )
    assert (
        actual_balance_update_query == expected_balance_update_query
    ), "Balance UPDATE query mismatch."
    assert new_balance == 700.0, "Final balance mismatch."


def test_buy_existing_stock(mock_cursor, mock_quote):
    """Test buying more of an existing stock."""
    mock_cursor.fetchone.side_effect = [
        (1, "test_user", "hashed_password", 1000.0),  # User data
        (1, 1, "AAPL", 150.0, 10),  # Existing stock
    ]

    new_balance = buy_stock(user_id=1, symbol="AAPL", quantity=5)

    # Assert stock quantity update
    expected_update_query = normalize_whitespace(
        "UPDATE user_stocks SET quantity = ? WHERE id = ?"
    )
    actual_update_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[2][0][0]
    )
    assert (
        actual_update_query == expected_update_query
    ), "Stock quantity UPDATE query mismatch."

    expected_args = (15, 1)  # New quantity and stock ID
    actual_args = mock_cursor.execute.call_args_list[2][0][1]
    assert actual_args == expected_args, f"Expected {expected_args}, got {actual_args}"

    # Assert final balance update
    expected_balance_update_query = normalize_whitespace(
        "UPDATE users SET balance = ? WHERE id = ?"
    )
    actual_balance_update_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[3][0][0]
    )
    assert (
        actual_balance_update_query == expected_balance_update_query
    ), "Balance UPDATE query mismatch."
    assert new_balance == 250.0, "Final balance mismatch."


def test_buy_stock_insufficient_balance(mock_cursor, mock_quote):
    """Test buying stock when user has insufficient balance."""
    mock_cursor.fetchone.side_effect = [
        (1, "test_user", "hashed_password", 100.0),  # User data
    ]

    with pytest.raises(ValueError, match="Insufficient balance"):
        buy_stock(user_id=1, symbol="AAPL", quantity=5)


######################################################
#
#    Sell Stock Tests
#
######################################################


def test_sell_stock_partial(mock_cursor, mock_quote):
    """Test selling part of a stock holding."""
    mock_cursor.fetchone.side_effect = [
        (1, "test_user", "hashed_password", 1000.0),  # User data
        (1, 1, "AAPL", 150.0, 10),  # Existing stock
    ]

    new_balance = sell_stock(user_id=1, symbol="AAPL", quantity=5)

    # Assert stock quantity update
    expected_update_query = normalize_whitespace(
        "UPDATE user_stocks SET quantity = ? WHERE id = ?"
    )
    actual_update_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[2][0][0]
    )
    assert (
        actual_update_query == expected_update_query
    ), "Stock quantity UPDATE query mismatch."

    expected_args = (5, 1)  # New quantity and stock ID
    actual_args = mock_cursor.execute.call_args_list[2][0][1]
    assert actual_args == expected_args, f"Expected {expected_args}, got {actual_args}"

    # Assert final balance update
    expected_balance_update_query = normalize_whitespace(
        "UPDATE users SET balance = ? WHERE id = ?"
    )
    actual_balance_update_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[3][0][0]
    )
    assert (
        actual_balance_update_query == expected_balance_update_query
    ), "Balance UPDATE query mismatch."
    assert new_balance == 1750.0, "Final balance mismatch."


def test_sell_stock_full(mock_cursor, mock_quote):
    """Test selling all stock holdings."""
    mock_cursor.fetchone.side_effect = [
        (1, "test_user", "hashed_password", 1000.0),  # User data
        (1, 1, "AAPL", 150.0, 10),  # Existing stock
    ]

    new_balance = sell_stock(user_id=1, symbol="AAPL", quantity=10)

    # Assert stock deletion
    expected_delete_query = normalize_whitespace("DELETE FROM user_stocks WHERE id = ?")
    actual_delete_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[2][0][0]
    )
    assert actual_delete_query == expected_delete_query, "Stock DELETE query mismatch."

    expected_args = (1,)  # Stock ID
    actual_args = mock_cursor.execute.call_args_list[2][0][1]
    assert actual_args == expected_args, f"Expected {expected_args}, got {actual_args}"

    # Assert final balance update
    expected_balance_update_query = normalize_whitespace(
        "UPDATE users SET balance = ? WHERE id = ?"
    )
    actual_balance_update_query = normalize_whitespace(
        mock_cursor.execute.call_args_list[3][0][0]
    )
    assert (
        actual_balance_update_query == expected_balance_update_query
    ), "Balance UPDATE query mismatch."
    assert new_balance == 2500.0, "Final balance mismatch."


def test_sell_stock_insufficient_quantity(mock_cursor, mock_quote):
    """Test selling stock when user does not have enough quantity."""
    mock_cursor.fetchone.side_effect = [
        (1, "test_user", "hashed_password", 1000.0),  # User data
        (1, 1, "AAPL", 150.0, 5),  # Existing stock
    ]

    with pytest.raises(ValueError, match="Insufficient stock quantity"):
        sell_stock(user_id=1, symbol="AAPL", quantity=10)


######################################################
#
#    Portfolio Tests
#
######################################################

def test_get_portfolio(mock_cursor):
    """Test getting a user's stock portfolio."""
    mock_cursor.fetchone.return_value = (1, "test_user", "hashed_password", 1000.0)
    mock_cursor.fetchall.return_value = [
        ("AAPL", 150.0, 5),
        ("GOOG", 200.0, 3),
    ]

    portfolio = get_portfolio(user_id=1)

    # Assert the correct SQL query was executed
    expected_query = normalize_whitespace(
        "SELECT symbol, bought_price, quantity FROM user_stocks WHERE user_id = ?"
    )
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "Portfolio SELECT query mismatch."

    # Assert the correct portfolio data was returned
    expected_portfolio = [
        {"symbol": "AAPL", "bought_price": 150.0, "quantity": 5},
        {"symbol": "GOOG", "bought_price": 200.0, "quantity": 3},
    ]
    assert portfolio == expected_portfolio, "Portfolio data mismatch."
    
def test_get_portfolio_no_user(mock_cursor):
    """Test getting a user's stock portfolio when the user does not exist."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="User with ID 1 not found"):
        get_portfolio(user_id=1)

def test_get_portfolio_database_error(mock_cursor):
    """Test getting a user's stock portfolio when a database error occurs."""
    mock_cursor.execute.side_effect = sqlite3.Error("Database error")

    with pytest.raises(ValueError, match="Error finding user: Database error"):
        get_portfolio(user_id=1)