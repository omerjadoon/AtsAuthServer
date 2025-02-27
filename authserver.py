from flask import Flask, request, redirect, jsonify
import random
import string
import requests
import time
import math
from flask_cors import CORS
import secrets
import base64
import hashlib

app = Flask(__name__)
CORS(app)

# In-memory database simulation
db = {}

APIGATEWAY_URL = 'http://localhost:5002'
ATSGATEWAY_URL = 'http://localhost'

def generate_auth_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def verify_pkce_pair(code_challenge_recieved , code_verifier):
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    
    if code_challenge == code_challenge_recieved : 
        print("Challenge Passed")
        return True 
    else :
        return False


def get_msisdn_from_public_ip(public_ip):
    try:
        print("Getting Private IP from Public IP")
        syslog_url = f"{ATSGATEWAY_URL}/syslog_public_ip?public_ip={public_ip}"
        response = requests.get(syslog_url)
        data = response.json()
        print(f"Response from syslog : {data}")
        
        response.raise_for_status()
       
        if not data.get("data"):
            return {"error": "No data found for the given public IP"}
        private_ip = data["data"][0].get("private_ip")
        print(f"Private IP : {private_ip}")
        if not private_ip:
            return {"error": "No IP found for the MSISDN"}
        
        print(f"Getting MSISDN from Private IP")
        msisdn_url = f"{ATSGATEWAY_URL}/get_msisdn?ipAddress={private_ip}"
        response = requests.get(msisdn_url)
        msisdn_data = response.json()
        print(f"Response from ATSGateway : {msisdn_data}")
        
        response.raise_for_status()

        msisdn = msisdn_data.get("msisdn")
        if not msisdn:
            return {"error": "MSISDN not found in response"}
        
        print(f"MSISDN found: {msisdn}")
        return {"msisdn": msisdn}
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    
def authorize_request(version):
    print(f"Authorization Request Received From the Client for v{version}")
    
    try:
        data = request.args
        print(f"Data from the Request ARGS : {data}")
    except Exception as e:
        pass
    
    try:
        data = request.json
        print(f"Data from the Request JSON : {data}")
    except Exception as e:
        pass
    
    redirect_uri = data.get('redirect_uri')
    code_challenge = data.get('code_challenge')
    code_challenge_method = data.get('code_challenge_method')
    scope = data.get('scope')
    client_id = data.get('client_id')
    
    if version == '3':
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)  # Get real IP
        print(f"IP Address from the Request Header : {ip_address}")
    elif version == '2':
        ip_address = "192.168.0.2"  # Fixed test IP
    else:
        ip_address = None
    
    if ip_address:
        phone_number = get_msisdn_from_public_ip(ip_address) 
        
        if phone_number.get("error"):
            print(f"Error getting phone number: {phone_number['error']}")
            return jsonify({"error": "Phone Number Not Found. Make sure you are on Mobile Data"}), 404
    
        phone_number = phone_number.get("msisdn")
    else:
        phone_number = "14251000000"
    
    
    
    print(f"Assuming After Network_Based_Authentication Phone_Number is : {phone_number}")
    
    auth_code = generate_auth_code()
    db[auth_code] = {
        'phone_number': phone_number, 
        'token': None,
        'code_challenge': code_challenge,
        'code_challenge_method': code_challenge_method,
        'scope': scope,
        'client_id': client_id
    }
    
    redirect_url = f"{redirect_uri}&AuthCode={auth_code}"
    print(f"Sending Back Redirect URL: {redirect_url}")
    return redirect(redirect_url, code=302)

@app.route('/auth/v3/authorize', methods=['GET'])
def authorize_v3():
    print("Authorization Request Received From the Client for v3 : IP Address from the Header")
    return authorize_request(version='3')

@app.route('/auth/v2/authorize', methods=['GET'])
def authorize_v2():
    print("Authorization Request Received From the Client for v2 : Fixed IP Address")
    return authorize_request(version='2')

@app.route('/auth/v1/authorize', methods=['GET'])
def authorize_v1():
    print("Authorization Request Received From the Client for v1 : Fixed Phone Number")
    return authorize_request(version='1')

@app.route('/auth/v1/token', methods=['POST'])
def token():
    auth_code = request.json.get('AuthCode')
    CodeVerifier = request.json.get('CodeVerifier')
    ClientSecret = request.json.get("ClientSecret")
    
    print(f"Request Recieved to get Auth Token based on AuthCode: {auth_code} , codeVerifer : {CodeVerifier} and ClientSecret : {ClientSecret}")
    
    if auth_code in db:
        
        codeChallenge = db[auth_code]['code_challenge']
        
        if verify_pkce_pair(codeChallenge , CodeVerifier):
            
            token = generate_token()
            db[auth_code]['token'] = token
            db[auth_code]['client_secret'] = ClientSecret

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
            return jsonify({"error" : "Code Challenge Not Verifed"}) , 400
            
    else:
        return jsonify({'error': 'Invalid AuthCode'}), 400


if __name__ == '__main__':
    app.run(port=5000)