import os
import logging
import requests

logger = logging.getLogger(__name__)

def quote_stock_by_symbol(symbol) -> dict:
    '''
    Get stock quote for a given symbol using the Alpha Vantage API
    
    Args:
        symbol (str): The symbol of the stock
    
    Returns:
        dict: The stock quote
    
    Raises:
        RuntimeError: If the request to AlphaVantage fails or returns an invalid response
        ValueError: If the symbol is invalid
    '''
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'
    
    try:
        # make a request to the AlphaVantage API
        logger.info("Requesting stock quote for %s", symbol)
        res = requests.get(url, timeout=5)
        data = res.json()
        
        if data['Global Quote'] == {}:
            raise ValueError('Invalid stock symbol')
    
        return data['Global Quote']
    except requests.exceptions.Timeout:
        logger.error("Request to AlphaVantage timed out.")
        raise RuntimeError("Request to AlphaVantage timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to AlphaVantage failed: %s", e)
        raise RuntimeError("Request to AlphaVantage failed: %s" % e)