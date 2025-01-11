# Yuval Shpitzer

import uuid # uuid module provides tools to generate unique id 
import requests # requests library is used to *make* HTTP requests to *other* servers
import re
from datetime import datetime
import os
import pymongo

# Flask: initializes the web application.
# request: Used to *handles* incoming requests to *my* Flask server
# jsonify: Used to create JSON responses easily, which are returned to the client.
from flask import Flask, request, jsonify

from pymongo import MongoClient

# Connect to MongoDB that runs in a container named 'mongo' on port 27017
client = MongoClient("mongodb://mongo:27017/")
db = client['myDB']

collection_name = os.getenv('COLLECTION_NAME', 'collection1')
collection = db[collection_name]

# The Flask object represents the web application. 
# __name__ is passed to Flask to set up paths and configurations correctly. It refers to the name of the current module.
app = Flask(__name__)

api_key = '0PXN/a3qirsKqQ+iGyUKtQ==JFuy0pu9YuMBLCks'
url = 'https://api.api-ninjas.com/v1/stockprice'

def validation(stock, rqst):
    if rqst == 'post':
        required = {
            'symbol': str,
            'purchase price': float,
            'shares': int,
        }

        not_required = {
            'name': str,
            'purchase date': str,
        }

    if rqst == 'put':
        required = {
            'id': str,
            'symbol': str,
            'name': str,
            'purchase date': str,
            'purchase price': float,
            'shares': int,
        }

        not_required = {}

    # validate required fields
    missing_fields = [field for field in required.keys() if field not in stock] # Determine missing fields
    if missing_fields:
        return False, {'error':f"Missing required fields: {', '.join(missing_fields)}"}

    # Ensure all values are of the correct type
    for key,value in required.items():
         if not isinstance(stock[key], value):
            return False, {"error": f"Invalid type for {key}: Expected {value.__name__}, got {type(stock[key]).__name__}"} # .__name__ retrieves the name of a type as a string

    if not_required:
        for key,value in not_required.items():
            if key in stock and stock[key] is not None:
                if not isinstance(stock[key], value):
                    return False, {"error": f"Invalid type for {key}: Expected {value.__name__}, got {type(stock[key]).__name__}"}

    # Ensure string values not empty
    for key,value in stock.items():
        if isinstance(stock[key], str):
            if not stock[key].strip():
                return False, {'error':f'{key} value cannot be empty'}

    # Validate symbol is in uppercase
    symbol = stock.get('symbol')
    if not symbol.isupper():
        return False, {'error':'symbol must be in uppercase'}
    
    # Validate purchase price is not negative
    price = stock.get('purchase price')
    if price < 0.0:
        return False, {"error": "Stock price can't be negative"}
    
    # Validate shares is not negative
    shares = stock.get('shares')
    if shares < 0:
        return False, {"error": "shares can't be negative"}

    # Validate purchase date format
    if 'purchase date' in stock and stock.get('purchase date') != 'NA': # check if the key 'purchase date' exists
        is_valid = date_validation(stock.get('purchase date'))
        if not is_valid:
            return False, {'error':'Invalid date format. Expected dd-mm-yyyy in valid range (e.g. months 01-12)'}

    return True, None


def date_validation(input_date):
    # ensures the input date matches the format - dd-mm-yyyy
    format = r"^\d{2}-\d{2}-\d{4}$"
    if not re.match(format, input_date):
        return False

    try:
        datetime.strptime(input_date, "%d-%m-%Y") # ensures the input date matches the format - day-month-year
        return True
        
    except ValueError:
        return False


@app.route('/stocks', methods=['POST']) # Flask route maps the URL /stocks to the add_stock function and specifies that it handles only POST requests.
def add_stock():
    # Checks whether the incoming request contains data in JSON format
    if not request.is_json:
        return jsonify({'error':'Unsupported Media Type'}), 415 # 415 = Unsupported Media Type

    try:
        stock = request.get_json() # Extracts the JSON payload from the incoming request and converts it into a Python dictionary.

        # if isinstance(stock, list):
        #     return add_stocks(stock)

        # validate required fields and types
        is_valid, err = validation(stock, 'post')
        if not is_valid:
            return jsonify(err), 400 # 400 = Bad Request

        # Prevent Duplicates
        exist_stock = collection.find_one( {'symbol': stock.get('symbol')})
        if exist_stock:
            return jsonify({'error':f'Duplicate stock entry: {exist_stock["symbol"]} already exists'}), 400
        # if any(stck['symbol'] == stock.get('symbol') for stck in portfolio):
        #     return jsonify({'error': f"Duplicate stock entry"}), 400

        stock_id = str(uuid.uuid4()) # Generates a unique ID for the new stock and converts it to a string.
        formatted_stock = {
            '_id': stock_id,
            'id': stock_id,
            'symbol': stock['symbol'],
            'purchase price': round(float(stock['purchase price']), 2),
            'shares': stock['shares'],
            'purchase date': stock.get('purchase date', 'NA'),
            'name': stock.get('name' , 'NA'),
        }
        
        # portfolio.append(formatted_stock)

        collection.insert_one(formatted_stock)
        return jsonify({'id':stock_id}), 201 # 201 = Created.

    #Catch any exceptions that occur in the try block.
    except Exception as e:
        return jsonify({'server error':str(e)}), 500 # 500 = Internal Server Error
    

@app.route('/stocks', methods=['GET'])
def get_stocks():
    try:
        stocks = list(collection.find({}, {'_id': 0}))
        querys = request.args # Retrieves any query parameters from the request URL as a dictionary-like object.
        if querys:
            # validate query parameters
            valid_keys = {'id', 'name', 'purchase date', 'purchase price', 'shares', 'symbol'}
            if any(key not in valid_keys for key in querys.keys()):
                return jsonify({'error': 'Invalid query parameter'}), 400


            # In Flask’s, query parameters values are always strings because Flask parses the query string and represents all values as strings, regardless of their apparent type. 
            filtered_stocks = [
                stock for stock in stocks
                # ensures that all conditions in the generator expression are True.
                # stock.get(key,'')).lower(): retrieve the value of the key from the stock dictionary and converts the string to lowercase. 
                # Defaults to an empty string ('') if the key is missing.
                if all(
                    str(stock.get(key,'')).lower() == value.lower() for key,value in querys.items()
                    )
            ]
            return jsonify(filtered_stocks), 200 # 200 = successfully executed

        # if the request doesn't have any query parameters
        return jsonify(stocks), 200

    except Exception as e: 
        return jsonify({'server error':str(e)}), 500


@app.route('/stocks/<id>', methods=['GET'])
def get_stock(id):
    try:
        # The second argument specifies which fields to include or exclude in the result
        stock = collection.find_one( {'_id': id}, {'_id': 0} )
        if not stock:
            return jsonify({'error':'Stock not found'}), 404

        return jsonify(stock), 200

    except Exception as e:
        return jsonify({'server error':str(e)}), 500


@app.route('/stocks/<id>', methods=['PUT'])
def update_stock(id):
    if not request.is_json:
        return jsonify({'error':'Unsupported Media Type'}), 415

    try:
        # Find the stock with the matching ID
        current_stock = collection.find_one( {'_id': id}, {'_id': 0} )
        if not current_stock:
            return jsonify({'error':'Stock not found'}), 404

        updated_stock = request.get_json() # Extracts the JSON payload from the incoming request and converts it into a Python dictionary
        is_valid, err = validation(updated_stock, 'put')
        if not is_valid:
            return jsonify(err), 400 # 400 = Bad Request

        if id != updated_stock['id']:
            return jsonify({'error':'id cannot be changed'}), 400

        # Prevent Duplicates
        exist_stock = collection.find_one( {'symbol': updated_stock.get('symbol'), '_id': {'$ne': id}})
        if exist_stock:
            return jsonify({'error':f'Duplicate stock entry: {exist_stock["symbol"]} already exists'}), 400

        collection.update_one({'_id': id}, {'$set': updated_stock})
        return jsonify({'id':id}), 200

    except Exception as e:
        return jsonify({'server error':str(e)}), 500

@app.route('/stocks/<id>', methods=['DELETE'])
def delete_stock(id):
    try:
        removed_stock = collection.delete_one( {'_id': id} )
        if removed_stock.deleted_count == 0:
            return jsonify({'error':'Stock not found'}), 404
        
        return '', 204 # 204 = No Content
        
    except Exception as e:
        return jsonify({'server error':str(e)}), 500

@app.route('/stock-value/<id>', methods=['GET'])
def get_stock_value(id):
    try:
        stock = collection.find_one( {'_id': id}, {'_id': 0} )
        if not stock:
            return jsonify({'error':'Stock not found'}), 404

        symbol = stock.get('symbol')
        api_url = '{}?ticker={}'.format(url, symbol)
        response = requests.get(api_url, headers={'X-Api-Key':f'{api_key}'})

        # Validate the API response
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch ticker price', 'details': response.text}), 500

        # Extract the price from the API response
        data = response.json()
        price = data.get('price')
        shares = float(stock.get('shares'))
        stock_value = float(shares * price)

        return jsonify({
            'symbol': symbol,
            'ticker': price,
            'stock value': stock_value
        }), 200
        
    except requests.exceptions.RequestException as e:
        # Handle API request exceptions
        return jsonify({'error': 'Failed to fetch ticker price', 'details': str(e)}), 500

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'server error':str(e)}), 500


@app.route('/portfolio-value', methods=['GET'])
def get_portfolio_value():
    try:
        portfolio = list(collection.find({}, {'_id': 0}))
        portfolio_value = 0
        for stock in portfolio:
            symbol = stock['symbol']
            api_url = '{}?ticker={}'.format(url, symbol)
            response = requests.get(api_url, headers={'X-Api-Key':f'{api_key}'})
                
            # Validate the API response
            if response.status_code != 200:
                return jsonify({'error': 'Failed to fetch ticker price', 'details': response.text}), 500

            # Extract the price from the API response
            data = response.json()
            price = data.get('price')
            shares = float(stock.get('shares'))
            portfolio_value += float(shares * price)

        date = datetime.today().strftime('%d-%m-%Y')

        return jsonify({
            'date': date,
            'portfolio value': round(portfolio_value, 2)
        }), 200
        
    except requests.exceptions.RequestException as e:
        # Handle API request exceptions
        return jsonify({'error': 'Failed to fetch ticker price', 'details': str(e)}), 500

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'server error':str(e)}), 500
    
@app.route('/kill', methods=['GET'])
def kill_container():
    print('Killing container')
    os._exit(1)

# routes for the nginx server
@app.route('/stocks1', methods=['GET'])
def get_stocks1():
    return get_stocks()

@app.route('/stocks1/<id>', methods=['GET'])
def get_stock1(id):
    return get_stock(id)

@app.route('/stocks2', methods=['GET'])
def get_stocks2():
    return get_stocks()

@app.route('/stocks2/<id>', methods=['GET'])
def get_stock2(id):
    return get_stock(id)
    

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000)) # default to 8000 if PORT is not set
    print(f'running stocks portfolio server on port {port}')
    app.run(host='0.0.0.0', port=8000, debug=True)