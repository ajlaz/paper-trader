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
        new_balance = user_stock_model.buy_stock(user_id, symbol, quantity)
        return make_response(
            jsonify(
                {"message": "Stock purchased successfully", "balance": new_balance}
            ),
            http.HTTPStatus.OK,
        )
    except ValueError as e:
        return make_response(jsonify({"error": str(e)}), http.HTTPStatus.BAD_REQUEST)
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
        new_balance = user_stock_model.sell_stock(user_id, symbol, quantity)
        return make_response(
            jsonify({"message": "Stock sold successfully", "balance": new_balance}),
            http.HTTPStatus.OK,
        )
    except ValueError as e:
        return make_response(jsonify({"error": str(e)}), http.HTTPStatus.BAD_REQUEST)
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
