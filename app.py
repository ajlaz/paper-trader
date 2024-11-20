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