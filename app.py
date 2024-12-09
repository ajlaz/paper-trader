from dotenv import load_dotenv
import http
import os
from flask import Flask, jsonify, make_response, Response, request

from paper_trader.models.user_model import create_user, find_user_by_username, update_password, check_password
from paper_trader.models import user_stock_model
from paper_trader.utils.stocks import quote_stock_by_symbol
from paper_trader.utils.sql_utils import check_database_connection

# Load environment variables
load_dotenv()

app = Flask(__name__)


# Health Checks
@app.route("/health", methods=["GET"])
def healthcheck():
    '''
    Health Check to ensure the service is running and healthy

    Returns:
        JSON response indicating the status of the service
    '''
    res = {"status": "ok"}

    app.logger.info("Health Check")
    return make_response(jsonify(res), http.HTTPStatus.OK)

@app.route("/db-check", methods=["GET"])
def db_check():
    '''
    Health Check to ensure the database connection is working

    Returns:
        JSON response indicating the status of the database connection
    '''
    try:
        check_database_connection()
        app.logger.info("Database connection is healthy")
        return make_response(jsonify({"status": "ok"}), http.HTTPStatus.OK)
    except Exception as e:
        app.logger.error("Database connection error: %s", str(e))
        return make_response(jsonify({"status": "error"}), http.HTTPStatus.INTERNAL_SERVER_ERROR)


# Authentication
@app.route("/auth/login", methods=["POST"])
def login():
    '''
    Login endpoint to authenticate the user

    Expects:
        JSON body with 'username' and 'password'
    
    Returns:
        JSON response indicating the status of the login
    '''
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = find_user_by_username(username)
    if user and check_password(user.password, password):
        app.logger.info('User %s logged in successfully.', username)
        return make_response(jsonify({'message': 'Login successfully'}), http.HTTPStatus.OK)
    
    app.logger.warning('Login failed for username: %s', username)
    return make_response(jsonify({'error': 'Invalid username or password'}), http.HTTPStatus.UNAUTHORIZED)


@app.route("/auth/create-account", methods=["POST"])
def register():
    '''
    Register endpoint to create a new user

    Expects: 
        JSON body with 'username', 'password', and optional 'balance'
    
    Returns:
        JSON response indicating the status of the registration
    '''
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    balance = data.get('balance', 100000.0)

    try:
        find_user_by_username(username)
        app.logger.warning('Registration failed: username %s already exists.', username)
        return make_response(jsonify({'error': 'Username already exists'}), http.HTTPStatus.BAD_REQUEST)
    except ValueError:
        pass
    
    user = create_user(username, password, balance)
    app.logger.info('User %s created successfully.', username)
    
    user = find_user_by_username(username)
    return make_response(jsonify({'message': 'User created successfully', 'user_id': user.id}), http.HTTPStatus.CREATED)

@app.route('/auth/change-password', methods=['PATCH'])
def change_password():
    '''
    Change password endpoint for an existing user.
    
    Expects:
        JSON body with 'username', 'old_password', and 'new_password'

    Returns:
        JSON response indicating the status of the password change
    '''
    
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    try:
        user = find_user_by_username(username)
        if check_password(user.password, old_password):    
            update_password(user.id, new_password)
            app.logger.info('Password updated for user %s.', username)
            return make_response(jsonify({'message': 'Password updated successfully'}), http.HTTPStatus.OK)
        app.logger.warning('Password change failed for username: %s', username)
        return make_response(jsonify({'error': 'Invalid username or password'}), http.HTTPStatus.UNAUTHORIZED)
    except ValueError:
        app.logger.warning('User not found: %s', username)
        return make_response(jsonify({'error': 'User not found'}), http.HTTPStatus.NOT_FOUND)
        

# Stock Management
@app.route("/users/<id>/stocks/buy", methods=["POST"])
def buy_stock(id):
    '''
    Buy endpoint to purchase stock
    '''
    data = request.json
    user_id = id
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


@app.route("/users/<id>/stocks/sell", methods=["POST"])
def sell_stock(id):
    '''
    Sell endpoint to sell stock
    '''
    data = request.json
    user_id = id
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
    '''
    Get stock quote for a given stock

    Returns:
        JSON response containing the stock quote
    '''
    try:
        quote = quote_stock_by_symbol(stock)
        return make_response(jsonify(quote), http.HTTPStatus.OK)
    except ValueError:
        return make_response(
            jsonify({"error": "Invalid stock symbol"}), http.HTTPStatus.BAD_REQUEST
        )


@app.route("/users/<id>/stocks/portfolio", methods=["GET"])
def get_portfolio(id):
    '''
    Get the portfolio of the user

    Returns:
        JSON response containing the user's portfolio
    '''
    portfolio = user_stock_model.get_portfolio(id)
    return make_response(jsonify(portfolio), http.HTTPStatus.OK)
    


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
