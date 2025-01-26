from flask import Flask, request, redirect, jsonify
import random
import string
import requests

app = Flask(__name__)

# In-memory database simulation
db = {}

APIGATEWAY_URL = 'http://localhost:5002'

def generate_auth_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

@app.route('/auth/v1/authorize', methods=['GET'])
def authorize():
    redirect_uri = request.args.get('redirect_uri')
    phone_number = "+14251000000"  # Test phone number
    auth_code = generate_auth_code()
    db[auth_code] = {'phone_number': phone_number, 'token': None}
    redirect_url = f"{redirect_uri}?AuthCode={auth_code}"
    return redirect(redirect_url, code=302)

@app.route('/auth/v1/token', methods=['POST'])
def token():
    auth_code = request.json.get('AuthCode')
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

        print(f"Token stored in APIGateway: {token}")
        return jsonify({
            'accessToken': token,
            'tokenType': 'Bearer',
            'expireIn': 1737530975  # Token expires in 1 hour (mock value)
        }), 200
    else:
        return jsonify({'error': 'Invalid AuthCode'}), 400

if __name__ == '__main__':
    app.run(port=5000)