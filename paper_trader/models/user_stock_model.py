from dataclasses import dataclass
import sqlite3
import logging
from paper_trader.models.user_model import find_user_by_id, update_user_balance
from paper_trader.utils.sql_utils import get_db_connection
from paper_trader.utils.logger import configure_logger
from paper_trader.utils.stocks import quote_stock_by_symbol

logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class UserStock:
    id: int
    user_id: int
    symbol: str
    bought_price: float
    quantity: int


def find_stock_by_user_and_symbol(user_id: int, symbol: str) -> UserStock:
    """
    Find a stock owned by a user based on the stock symbol
    
    Args:
        user_id (int): The user's ID
        symbol (str): The stock symbol
    
    Returns:
        UserStock: The UserStock object corresponding to the user and symbol
    
    Raises:
        sqlite3.Error: If there is a database error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, symbol, bought_price, quantity
                FROM user_stocks
                WHERE user_id = ? AND symbol = ?
            """,
                (user_id, symbol),
            )
            stock = cursor.fetchone()
            if stock:
                return UserStock(*stock)
            return None
    except sqlite3.Error as e:
        logger.error(
            "Database error finding stock for user %s and symbol %s", user_id, symbol
        )
        raise e


def update_stock_quantity(stock_id: int, new_quantity: int) -> None:
    """
    Update the quantity of an existing stock
    
    Args:
        stock_id (int): The stock ID
        new_quantity (int): The new quantity
    
    Raises:
        sqlite3.Error: If there is a database error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE user_stocks
                SET quantity = ?
                WHERE id = ?
            """,
                (new_quantity, stock_id),
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database error updating stock %s", stock_id)
        raise e


def add_new_stock(user_id: int, symbol: str, bought_price: float, quantity: int) -> None:
    """
    Add a new stock entry for a user
    
    Args:
        user_id (int): The user's ID
        symbol (str): The stock symbol
        bought_price (float): The price at which the stock was bought
        quantity (int): The quantity of the stock
    
    Raises:
        sqlite3.Error: If there is a database error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_stocks (user_id, symbol, bought_price, quantity)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, symbol, bought_price, quantity),
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database error adding new stock for user %s", user_id)
        raise e


def remove_stock(stock_id: int) -> None:
    """
    Remove a stock entry when its quantity reaches zero
    
    Args:
        stock_id (int): The stock ID

    Raises:
        sqlite3.Error: If there is a database error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_stocks WHERE id = ?", (stock_id,))
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database error removing stock %s", stock_id)
        raise e


def buy_stock(user_id: int, symbol: str, quantity: float) -> float:
    """
    Handles the business logic for buying stocks
    
    Args:
        user_id (int): The user's ID
        symbol (str): The stock symbol
        quantity (float): The quantity of the stock to buy
    
    Returns:
        float: The user's new balance
        
    Raises:
        ValueError: If the user is not found, the balance is insufficient, or the stock price is not found
    """
    # Get user details
    user = find_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")

    # Fetch stock price
    quote = quote_stock_by_symbol(symbol)
    stock_price = float(quote["05. price"])

    # Calculate total cost
    total_cost = stock_price * quantity

    # Check user's balance
    if user.balance < total_cost:
        raise ValueError("Insufficient balance")

    # Find existing stock or add a new one
    stock = find_stock_by_user_and_symbol(user_id, symbol)
    if stock:
        new_quantity = stock.quantity + quantity
        update_stock_quantity(stock.id, new_quantity)
    else:
        add_new_stock(user_id, symbol, stock_price, quantity)

    # Deduct cost from user's balance
    new_balance = user.balance - total_cost
    update_user_balance(user_id, new_balance)

    return new_balance


def sell_stock(user_id: int, symbol: str, quantity: float) -> float:
    """
    Handles the business logic for selling stocks
    
    Args:
        user_id (int): The user's ID
        symbol (str): The stock symbol
        quantity (float): The quantity of the stock to sell
    
    Returns:
        float: The user's new balance
    
    Raises:
        ValueError: If the user is not found, the stock is not found, or the quantity is insufficient.
    """
    # Get user details
    user = find_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")

    # Find the user's stock
    stock = find_stock_by_user_and_symbol(user_id, symbol)
    if not stock or stock.quantity < quantity:
        raise ValueError("Insufficient stock quantity")

    # Calculate revenue from the sale
    quote = quote_stock_by_symbol(symbol)
    stock_price = float(quote["05. price"])
    revenue = stock_price * quantity

    # Update stock quantity or remove the stock
    new_quantity = stock.quantity - quantity
    if new_quantity > 0:
        update_stock_quantity(stock.id, new_quantity)
    else:
        remove_stock(stock.id)

    # Update user's balance
    new_balance = user.balance + revenue
    update_user_balance(user_id, new_balance)

    return new_balance

def get_portfolio(user_id: str) -> dict:
    """
    Gets the user's stock portfolio
    
    Args:
        user_id (str): The user's ID
    
    Returns:
        dict: The user's stock portfolio
    
    Raises:
        ValueError: If the user is not found
        sqlite3.Error: If there is a database error
    """
    
    try:
        with get_db_connection() as conn:
            user = find_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT symbol, bought_price, quantity
                FROM user_stocks
                WHERE user_id = ?
            """,
                (user_id,),
            )
            stocks = cursor.fetchall()
            portfolio_response = {
                "username": user.username,
                "balance": user.balance,
                "total_portfolio_value": 0,
            }
            portfolio = []
            for stock in stocks:
                portfolio.append(
                    {
                        "symbol": stock[0],
                        "bought_price": stock[1],
                        "quantity": stock[2],
                        "total_value": stock[1] * stock[2],
                    }
                )
                portfolio_response["total_portfolio_value"] += stock[1] * stock[2]
            portfolio_response["stocks"] = portfolio
            return portfolio_response
    except sqlite3.Error as e:
        logger.error("Database error finding user by id %s", user_id)
        raise ValueError(f"Error finding user: {e}") from e
            