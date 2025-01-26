from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APIGATEWAY_URL = 'http://localhost:5002'

@app.route('/shush/number-verification/v0/verify', methods=['POST'])
def verify():
    # Log the incoming request
    print(f"Incoming request headers: {request.headers}")
    print(f"Incoming request body: {request.json}")

    # Validate Authorization header
    access_token = request.headers.get('Authorization')
    if not access_token or not access_token.startswith("Bearer "):
        print("Invalid or missing Authorization header")
        return jsonify({'error': 'Invalid or missing Authorization header'}), 400

    # Validate phoneNumber in request body
    phone_number = request.json.get('phoneNumber')
    if not phone_number:
        print("Missing phoneNumber in request body")
        return jsonify({'error': 'Missing phoneNumber in request body'}), 400

    # Forward the token to APIGateway
    headers = {'Authorization': access_token}
    print(f"Sending request to APIGateway with token: {access_token}")
    response = requests.post(f"{APIGATEWAY_URL}/camara/number-verification/v0/verify", headers=headers)

    if response.status_code != 200:
        print(f"APIGateway verification failed: {response.status_code} - {response.text}")
        return jsonify({'error': 'APIGateway verification failed'}), 400

    device_phone_number = response.json().get('devicePhoneNumber')
    print(f"Device phone number from APIGateway: {device_phone_number}")

    # Compare phone numbers
    if device_phone_number == phone_number:
        return jsonify({'devicePhoneNumberVerified': 'yes'}), 200
    else:
        return jsonify({'devicePhoneNumberVerified': 'no'}), 200

if __name__ == '__main__':
    app.run(port=5003)