from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import time
import secrets
import base64
import hashlib

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUTH_SERVER_URL = 'http://localhost:5000'
BACKEND_REDIRECT_URL = 'http://localhost:5001/callback'
SHUSHSERVER_URL = 'http://localhost:5003'

CLIENT_ID = "s6BhdRkqt3"
CLIENT_Secret = "3s7df8GFsDk9nvzPqL6Yv7VWLJx9I8LXkF7x4YKXnW3A"

# In-memory log storage (for simplicity)
logs = []
db = {}

def log_step(step, details):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {step}: {details}"
    logs.append(log_entry)
    logger.info(log_entry)
    
def generate_nonce(length=16):
    """Generate a URL-safe base64 encoded nonce."""
    random_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

def generate_pkce_pair():
    """Generate a PKCE Code Verifier and its corresponding Code Challenge."""
    
    code_verifier = secrets.token_urlsafe(64)

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge

@app.route('/verify', methods=['POST'])
def verify():
    logs.clear()  # Clear logs for a new verification process
    phone_number = request.json.get('phoneNumber')
    log_step("Step 1", f"Received phone number to Start Verification : {phone_number}")
    
    nonce = generate_nonce()
    code_verifier , code_challenge = generate_pkce_pair()
    
    print("--------------------------------------------------------------------------")
    print(f"Generated Nonce: {nonce}")
    print(f"Generated Code Verifier: {code_verifier} and Code Challenge: {code_challenge}")
    
    db[nonce] = {
        "phonenumber": phone_number,
        "code_verifier": code_verifier,
        "code_challenge": code_challenge
    }
    
    # Step 2: Redirect to auth server for authorization
    BACKEND_REDIRECT_URL_state = BACKEND_REDIRECT_URL + f"?state={nonce}"
    url_parameters = f"code_challenge={code_challenge}&redirect_uri={BACKEND_REDIRECT_URL_state}&code_challenge_method=S256&scope=number_verification&client_id={CLIENT_ID}"
    auth_url = f"{AUTH_SERVER_URL}/auth/v3/authorize?{url_parameters}"
    
    print(f"Sending back auth-server link to the Client: {auth_url}")
    print("--------------------------------------------------------------------------")
    
    log_step("Step 2", f"Sending back auth-server link to the Client: {auth_url}")
    
    # Can be changed to 302 redirect
    return jsonify({'auth_url': auth_url, 'logs': logs}), 200




@app.route('/callback', methods=['GET'])
def callback():
    auth_code = request.args.get('AuthCode')
    nonce = request.args.get('state')
    
    phone_number = db[nonce]["phonenumber"]
    code_verifier = db[nonce]["code_verifier"]
    
    log_step("Step 3", f"Received AuthCode from auth server: {auth_code} and phone number From the State: {phone_number}")

    # Step 4: Exchange AuthCode for Token
    token_url = f"{AUTH_SERVER_URL}/auth/v1/token"
    log_step("Step 4", f"Exchanging AuthCode for token at: {token_url}")
    response = requests.post(token_url, json={'AuthCode': auth_code , 'CodeVerifier':code_verifier , 'ClientSecret':CLIENT_Secret})

    if response.status_code == 200:
        token_data = response.json()
        log_step("Step 5", f"Access Token Recieved: {token_data}")

        # Step 6: Verify token with ShushServer
        shush_url = f"{SHUSHSERVER_URL}/shush/number-verification/v0/verify"
        headers = {'Authorization': f"Bearer {token_data['accessToken']}"}
        body = {'phoneNumber': phone_number}
        shush_response = requests.post(shush_url, headers=headers, json=body)

        if shush_response.status_code == 200:
            verification_result = shush_response.json().get('devicePhoneNumberVerified')
            log_step("Step 6", f"ShushServer verification result: {verification_result}")
            return jsonify({'status': 'Verification completed', 'verification_result': verification_result, 'logs': logs}), 200
        else:
            log_step("Step 6", "ShushServer verification failed")
            return jsonify({'error': 'ShushServer verification failed', 'logs': logs}), 400
    else:
        log_step("Step 5", "Verification failed: Invalid AuthCode")
        return jsonify({'error': 'Verification failed', 'logs': logs}), 400

if __name__ == '__main__':
    app.run(port=5001)