import pytest
import requests

from paper_trader.utils.stocks import quote_stock_by_symbol

RANDOM_SYMBOL = 'AAPL'

@pytest.fixture
def mock_quote(mocker):
    #patch the requests.get method
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'Global Quote': {
            '01. symbol': RANDOM_SYMBOL,
            '02. open': '116.2500',
            '03. high': '116.4000',
            '04. low': '115.5700',
            '05. price': '116.0300',
            '06. volume': '28239269',
            '07. latest trading day': '2020-10-30',
            '08. previous close': '115.3200',
            '09. change': '0.7100',
            '10. change percent': '0.6159%'
        }
    }
    mocker.patch('os.getenv', return_value='api-key')
    mocker.patch('requests.get', return_value=mock_response)
    return mock_response

def test_quote_stock_by_symbol(mock_quote):
    '''Simulate a valid request to AlphaVantage.'''
    quote = quote_stock_by_symbol(RANDOM_SYMBOL)
    
    assert quote['01. symbol'] == RANDOM_SYMBOL,  f'Expected {RANDOM_SYMBOL} but got {quote["01. symbol"]}'
    
    requests.get.assert_called_once_with(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={RANDOM_SYMBOL}&apikey=api-key', timeout=5)

def test_quote_stock_by_symbol_request_failure(mocker):
    """Simulate  a request failure."""
    
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to AlphaVantage failed: Connection error"):
        quote_stock_by_symbol(RANDOM_SYMBOL)

def test_quote_stock_by_symbol_timeout(mocker):
    """Simulate  a timeout."""
    
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to AlphaVantage timed out."):
        quote_stock_by_symbol(RANDOM_SYMBOL)

def test_quote_stock_by_symbol_invalid_response(mocker):
    """Simulate an invalid response (empty Global Quote)."""
    
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'Global Quote': {}
    }
    mocker.patch('requests.get', return_value=mock_response)

    with pytest.raises(ValueError, match="Invalid stock symbol"):
        quote_stock_by_symbol(RANDOM_SYMBOL)