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

api_key = '0PXN/a3qirsKqQ+iGyUKtQ==JFuy0pu9YuMBLCks'
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
        querys = request.args or {} # Ensures that even if request.args were None (highly unlikely in Flask), it defaults to an empty dictionary.
        if querys:
            is_valid, err = querys_validation(querys)
            if not is_valid:
                return jsonify(err), 400
            
            # portfolio_querys_values = querys.getlist('portfolio') # This list can be: ['stocks1'], ['stocks2'], ['stocks1', 'stocks2'], or []
            # if portfolio_querys_values == ['stocks1']:
            #     portfolio1 = requests.get('http://stocks-service:8000/stocks')
            #     portfolio1.raise_for_status()
            #     collection = portfolio1.json()
            #     capital_gains = portfolio_val(collection, querys)
            #     return jsonify(capital_gains), 200

            # elif portfolio_querys_values == ['stocks2']:
            #     portfolio2 = requests.get('http://stocks2:8000/stocks')
            #     portfolio2.raise_for_status()
            #     collection = portfolio2.json()
            #     capital_gains = portfolio_val(collection, querys)
            #     return jsonify(capital_gains), 200

        # collection = both_services_use()
        response = requests.get('http://stocks-service:8000/stocks')
        response.raise_for_status()
        collection = response.json()
        capital_gains = portfolio_val(collection, querys)
        return jsonify(capital_gains), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# def both_services_use():
#     portfolio1 = requests.get('http://stocks1-a:8000/stocks')
#     portfolio1.raise_for_status()
#     collection1 = portfolio1.json()

#     portfolio2 = requests.get('http://stocks2:8000/stocks')
#     portfolio2.raise_for_status()
#     collection2 = portfolio2.json()

#     collection = collection1 + collection2
#     return collection
    
def portfolio_val(collection, querys):
    capital_gains = 0
    if 'numsharesgt' in querys and 'numshareslt' in querys:
        numsharesgt = int(querys['numsharesgt'])
        numshareslt = int(querys['numshareslt'])
        if numsharesgt == numshareslt:
            portfolio = [stock for stock in collection if stock.get('shares') == numsharesgt]
        else:
            portfolio = [stock for stock in collection if numsharesgt < stock.get('shares') < numshareslt]

    elif 'numsharesgt' in querys and 'numshareslt' not in querys:
        numsharesgt = int(querys['numsharesgt'])
        portfolio = [stock for stock in collection if stock.get('shares') > numsharesgt]

    elif 'numshareslt' in querys and 'numsharesgt' not in querys:
        numshareslt = int(querys['numshareslt'])
        portfolio = [stock for stock in collection if stock.get('shares') < numshareslt]

    else:
        portfolio = collection

    for stock in portfolio:
        symbol = stock['symbol']
        current_stock_price = fetch_stock_price(symbol)
        stock_capital_gain = calc_capital_gain(stock, current_stock_price)
        capital_gains += stock_capital_gain

    capital_gains = round(capital_gains, 2)
    return {'capital_gains': capital_gains}
    
def fetch_stock_price(symbol):
        api_url = '{}?ticker={}'.format(url, symbol)
        response = requests.get(api_url, headers={'X-Api-Key':f'{api_key}'})
        response.raise_for_status()
        return response.json().get('price')
            
def calc_capital_gain(stock, current_price):
    shares = float(stock.get('shares'))
    # current_stock_value = float(shares * current_price)
    stock_purchase_price = float(stock.get('purchase price'))
    return float((current_price - stock_purchase_price) * shares)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080)) # default to 8080 if PORT is not set
    print(f'running stocks portfolio server on port {port}')
    app.run(host='0.0.0.0', port=port, debug=True)