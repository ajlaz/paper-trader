from dotenv import load_dotenv
import http
import os
from flask import Flask, jsonify, make_response, Response, request

from paper_trader.models.user_model import find_user_by_id, update_user_balance
from paper_trader.models.user_stock_model import (
    find_stock_by_user_and_symbol,
    update_stock_quantity,
    add_new_stock,
    remove_stock,
)

from utils.stocks import quote_stock_by_symbol

# Load environment variables
load_dotenv()

app = Flask(__name__)


# Health Checks
@app.route("/health", methods=["GET"])
def healthcheck():
    """
    Health Check to ensure the service is running and healthy

    Returns:
        JSON response indicating the status of the service
    """
    res = {"status": "ok"}

    app.logger.info("Health Check")
    return make_response(jsonify(res), http.HTTPStatus.OK)


# Authentication
@app.route("/auth/login", methods=["POST"])
def login():
    """
    Login endpoint to authenticate the user

    Returns:
        JSON response indicating the status of the login
    """
    pass


@app.route("/auth/create-account", methods=["POST"])
def register():
    """
    Register endpoint to create a new user

    Returns:
        JSON response indicating the status of the registration
    """
    pass


@app.route("/auth/change-password", methods=["PATCH"])

# Stock Management
@app.route("/stocks/buy", methods=["POST"])
def buy_stock():
    """
    Buy endpoint to purchase stock
    """
    data = request.json
    user_id = data.get("user_id")
    symbol = data.get("symbol")
    quantity = data.get("quantity")

    if not user_id or not symbol or not quantity:
        return make_response(
            jsonify({"error": "Missing required fields"}), http.HTTPStatus.BAD_REQUEST
        )
    if quantity <= 0:
        return make_response(
            jsonify({"error": "Quantity must be greater than 0"}),
            http.HTTPStatus.BAD_REQUEST,
        )

    try:
        # Get user details
        user = find_user_by_id(user_id)
        if not user:
            return make_response(
                jsonify({"error": "User not found"}), http.HTTPStatus.NOT_FOUND
            )

        # Fetch stock price
        quote = quote_stock_by_symbol(symbol)
        stock_price = float(quote["05. price"])

        # Calculate total cost
        total_cost = stock_price * quantity

        # Check user's balance
        if user.balance < total_cost:
            return make_response(
                jsonify({"error": "Insufficient balance"}), http.HTTPStatus.BAD_REQUEST
            )

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

        return make_response(
            jsonify(
                {"message": "Stock purchased successfully", "balance": new_balance}
            ),
            http.HTTPStatus.OK,
        )
    except ValueError as e:
        return make_response(jsonify({"error": str(e)}), http.HTTPStatus.BAD_REQUEST)
    except RuntimeError as e:
        return make_response(
            jsonify({"error": str(e)}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        app.logger.error("Unexpected error: %s", str(e))
        return make_response(
            jsonify({"error": "Internal server error"}),
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@app.route("/stocks/sell", methods=["POST"])
def sell_stock():
    """
    Sell endpoint to sell stock
    """
    data = request.json
    user_id = data.get("user_id")
    symbol = data.get("symbol")
    quantity = data.get("quantity")

    if not user_id or not symbol or not quantity:
        return make_response(
            jsonify({"error": "Missing required fields"}), http.HTTPStatus.BAD_REQUEST
        )
    if quantity <= 0:
        return make_response(
            jsonify({"error": "Quantity must be greater than 0"}),
            http.HTTPStatus.BAD_REQUEST,
        )

    try:
        # Get user details
        user = find_user_by_id(user_id)
        if not user:
            return make_response(
                jsonify({"error": "User not found"}), http.HTTPStatus.NOT_FOUND
            )

        # Find the user's stock
        stock = find_stock_by_user_and_symbol(user_id, symbol)
        if not stock or stock.quantity < quantity:
            return make_response(
                jsonify({"error": "Insufficient stock quantity"}),
                http.HTTPStatus.BAD_REQUEST,
            )

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

        return make_response(
            jsonify({"message": "Stock sold successfully", "balance": new_balance}),
            http.HTTPStatus.OK,
        )
    except ValueError as e:
        return make_response(jsonify({"error": str(e)}), http.HTTPStatus.BAD_REQUEST)
    except RuntimeError as e:
        return make_response(
            jsonify({"error": str(e)}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        app.logger.error("Unexpected error: %s", str(e))
        return make_response(
            jsonify({"error": "Internal server error"}),
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@app.route("/stocks/quote/<stock>", methods=["GET"])
def get_stock_quote(stock):
    """
    Get stock quote for a given stock

    Returns:
        JSON response containing the stock quote
    """
    try:
        quote = quote_stock_by_symbol(stock)
        return make_response(jsonify(quote), http.HTTPStatus.OK)
    except ValueError:
        return make_response(
            jsonify({"error": "Invalid stock symbol"}), http.HTTPStatus.BAD_REQUEST
        )


@app.route("/stocks/portfolio", methods=["GET"])
def get_portfolio():
    """
    Get the portfolio of the user

    Returns:
        JSON response containing the user's portfolio
    """
    pass


if __name__ == "__main__":
    # check if HTTP variables are set in the environment
    if os.getenv("HTTP_HOST"):
        host = os.getenv("HTTP_HOST")
    else:
        host = "0.0.0.0"
    if os.getenv("HTTP_PORT"):
        port = int(os.getenv("HTTP_PORT"))
    else:
        port = 5000

    app.run(debug=True, host=host, port=port)
