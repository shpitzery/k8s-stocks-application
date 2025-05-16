# Yuval Shpitzer

import uuid # uuid module provides tools to generate unique id 
import requests # requests library is used to *make* HTTP requests to *other* servers
import re
from datetime import datetime
import os

# Flask: initializes the web application.
# request: Used to *handles* incoming requests to *my* Flask server
# jsonify: Used to create JSON responses easily, which are returned to the client.
from flask import Flask, request, jsonify

# The Flask object represents the web application. 
# __name__ is passed to Flask to set up paths and configurations correctly. It refers to the name of the current module.
app = Flask(__name__)

api_key = '<your api key>'
url = 'https://api.api-ninjas.com/v1/stockprice'

def querys_validation(querys):
    # validate query parameters
    valid_keys = {'numsharesgt', 'numshareslt'}
    if any(key not in valid_keys for key in querys.keys()):
        return False, {'error': 'Invalid query parameter'}
    
    # Validate querys values.
    # querys key,value are always strings
    for key in querys.keys():
        values = querys.getlist(key) # Get all values for the key

        for value in values:
            if key in ['numsharesgt', 'numshareslt']:
                try:
                    int(value)
                    if key == 'numshareslt' and int(value) <= 0:
                        return False, {'error': f'Invalid value for {key}: number of shares cannot be negative'}
                except ValueError:
                    return False, {'error': f'Invalid value for {key}: must be an integer'}
                
        # Check for duplicates by converting the list of values to a set. 
        # A set removes duplicates, so if the length of the set is less than the list, duplicates exist.
        if len(values) > len(set(values)):
            return False, {'error': f'Duplicate values for {key}'}
        
    return True, None
    

@app.route('/capital-gains', methods=['GET'])
def get_capital_gains():
    try:
        app.logger.info('Received request with query parameters: %s', request.args)
        querys = request.args or {} # Ensures that even if request.args were None (highly unlikely in Flask), it defaults to an empty dictionary.

        if querys:
            is_valid, err = querys_validation(querys)
            if not is_valid:
                return jsonify(err), 400

        response = requests.get('http://stocks-service:8000/stocks')
        response.raise_for_status()

        app.logger.info(f'Stocks service response: {response.text}')

        collection = response.json()
        if not isinstance(collection, list):
            app.logger.error('Expected list from stocks service, got: %s', type(collection))
            return jsonify({'error': 'Invalid response from stocks service'}), 500

        capital_gains = portfolio_val(collection, querys)
        return jsonify(capital_gains), 200
            
    except requests.RequestException as e:
        app.logger.error(f'Failed to fetch stocks data: {str(e)}')
        return jsonify({'error': f'Failed to fetch stocks data: {str(e)}'}), 503
    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    
def portfolio_val(collection, querys):
    try:
        app.logger.info(f'Calculating gains for {len(collection)} stocks')
        capital_gains = 0
        
        # Filter the portfolio based on query parameters
        portfolio = filter_portfolio(collection, querys)
        app.logger.info(f'Processing {len(portfolio)} stocks after filtering')

        for stock in portfolio:
            symbol = stock['symbol']
            shares = float(stock['shares'])
            purchase_price = float(stock['purchase price'])

            current_stock_price = fetch_stock_price(symbol)
            if current_stock_price is None:
                app.logger.warning(f'Skipping {symbol} - unable to fetch current price')
                continue

            stock_capital_gain = (current_stock_price - purchase_price) * shares
            capital_gains += stock_capital_gain
            
            app.logger.info(f'Stock {symbol}: Purchase: ${purchase_price}, Current: ${current_stock_price}, Gain: ${stock_capital_gain}')

        return {'capital_gains': round(capital_gains, 2)}
        
    except Exception as e:
        app.logger.error(f'Error in calculate_portfolio_gains: {str(e)}', exc_info=True)
        raise

def filter_portfolio(collection, querys):
    if 'numsharesgt' in querys and 'numshareslt' in querys:
        numsharesgt = int(querys.get('numsharesgt'))
        numshareslt = int(querys.get('numshareslt'))
        if numsharesgt == numshareslt:
            return [stock for stock in collection if stock['shares'] == numsharesgt]
        return [stock for stock in collection if numsharesgt < stock['shares'] < numshareslt]
    
    if 'numsharesgt' in querys:
        numsharesgt = int(querys.get('numsharesgt'))
        return [stock for stock in collection if stock['shares'] > numsharesgt]
    
    if 'numshareslt' in querys:
        numshareslt = int(querys.get('numshareslt'))
        return [stock for stock in collection if stock['shares'] < numshareslt]
    
    return collection
    
def fetch_stock_price(symbol):
    try:
        api_url = f'{url}?ticker={symbol}'
        response = requests.get(api_url, headers={'X-Api-Key': api_key})
        response.raise_for_status()

        data = response.json()
        app.logger.info(f'API response for {symbol}: {data}')
        
        # Check if data is a list and handle accordingly
        if isinstance(data, list):
            if not data:  # Empty list
                app.logger.error(f'Empty response for symbol {symbol}')
                return None
            price_data = data[0]  # Take first item if list
        else:
            price_data = data  # Use as is if not list
            
        if 'price' not in price_data:
            app.logger.error(f'No price data found for {symbol}')
            return None
            
        return float(price_data['price'])
    
    except requests.RequestException as e:
        app.logger.error(f'API request failed for {symbol}: {str(e)}')
        return None
    except (ValueError, KeyError) as e:
        app.logger.error(f'Error parsing price data for {symbol}: {str(e)}')
        return None
    except Exception as e:
        app.logger.error(f'Unexpected error getting price for {symbol}: {str(e)}')
        return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080)) # default to 8080 if PORT is not set
    print(f'running stocks portfolio server on port {port}')
    app.run(host='0.0.0.0', port=port, debug=True)
