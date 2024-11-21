from dotenv import load_dotenv
import http
import os
from flask import Flask, jsonify, make_response, Response, request

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Health Checks
@app.route('/health', methods=['GET'])
def healthcheck():
    '''
    Health Check to ensure the service is running and healthy
    
    Returns:
        JSON response indicating the status of the service
    '''
    res = {
        'status': 'ok'
        }
    
    app.logger.info('Health Check')
    return make_response(jsonify(res), http.HTTPStatus.OK)

# Authentication
@app.route('/auth/login', methods=['POST'])
def login():
    '''
    Login endpoint to authenticate the user
    
    Returns:
        JSON response indicating the status of the login
    '''
    pass

@app.route('/auth/create-account', methods=['POST'])
def register():
    '''
    Register endpoint to create a new user
    
    Returns:
        JSON response indicating the status of the registration
    '''
    pass

@app.route('/auth/change-password', methods=['PATCH'])

# Stock Management
@app.route('/stocks/buy', methods=['POST'])
def buy_stock():
    '''
    Buy endpoint to purchase stock
    
    Returns:
        JSON response indicating the status of the purchase
    '''
    pass

@app.route('/stocks/sell', methods=['POST'])
def sell_stock():
    '''
    Sell endpoint to sell stock
    
    Returns:
        JSON response indicating the status of the sale
    '''
    pass

@app.route('/stocks/quote/<stock>', methods=['GET'])
def get_stock_quote(stock):
    '''
    Get stock quote for a given stock
    
    Returns:
        JSON response containing the stock quote
    '''
    pass

@app.route('/stocks/portfolio', methods=['GET'])
def get_portfolio():
    '''
    Get the portfolio of the user
    
    Returns:
        JSON response containing the user's portfolio
    '''
    pass

if __name__ == '__main__':
    # check if HTTP variables are set in the environment
    if os.getenv('HTTP_HOST'):
        host = os.getenv('HTTP_HOST')
    else:
        host = '0.0.0.0'
    if os.getenv('HTTP_PORT'):
        port = int(os.getenv('HTTP_PORT'))
    else:
        port = 5000
        
    app.run(debug=True, host=host, port=port)