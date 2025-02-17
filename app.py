from flask import Flask, request, redirect, jsonify
import random
import string
import requests
import time
import math
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory database simulation
db = {}

APIGATEWAY_URL = 'http://localhost:5002'

def generate_auth_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

@app.route('/auth/v1/authorize', methods=['GET'])
def authorize():
    print("Authorization Request Received From the Client")
    redirect_uri = request.args.get('redirect_uri')
    phone_number = "14251000000"  # Test phone number ( FIXED ) (Assuming this Number After NBA)
    print(f"Assuming After Network_Based_Authentication Phone_Number is : {phone_number}")
    print("Generating AuthCode")
    auth_code = generate_auth_code()
    db[auth_code] = {'phone_number': phone_number, 'token': None}
    redirect_url = f"{redirect_uri}&AuthCode={auth_code}"
    print(f"Sending Back Redirect URL: {redirect_url}")
    return redirect(redirect_url, code=302)

@app.route('/auth/v1/token', methods=['POST'])
def token():
    auth_code = request.json.get('AuthCode')
    
    print(f"Request Recieved to get Auth Token based on AuthCode: {auth_code}")
    
    if auth_code in db:
        
        token = generate_token()
        db[auth_code]['token'] = token

        # Store token in APIGateway's database
        response = requests.post(
            f"{APIGATEWAY_URL}/camara/number-verification/v0/add",
            json={'token': token, 'phoneNumber': db[auth_code]['phone_number']}
        )

        if response.status_code != 200:
            print(f"Failed to store token in APIGateway: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to store token in APIGateway'}), 500

        # Time stamp for token expiration after 1 hour
        ts = time.time()
        token_expiration = ts + 3600
        token_expiration = math.floor(token_expiration)
        
        print(f"Returning Token : {token}")
        
        return jsonify({
            'accessToken': token,
            'tokenType': 'Bearer',
            'expireIn': token_expiration
        }), 200
    else:
        return jsonify({'error': 'Invalid AuthCode'}), 400

if __name__ == '__main__':
    app.run(port=5000)