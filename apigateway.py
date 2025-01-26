from flask import Flask, request, jsonify

app = Flask(__name__)

# Simulated database (mocked for testing)
db = {}

@app.route('/camara/number-verification/v0/verify', methods=['POST'])
def verify():
    access_token = request.headers.get('Authorization')
    if not access_token or not access_token.startswith("Bearer "):
        return jsonify({'error': 'Invalid token'}), 400

    token = access_token.split(" ")[1]
    device_phone_number = db.get(token)

    if device_phone_number:
        return jsonify({'devicePhoneNumber': device_phone_number}), 200
    else:
        return jsonify({'error': 'Token not found'}), 404

# Endpoint to add token and phone number to the database (for testing)
@app.route('/camara/number-verification/v0/add', methods=['POST'])
def add_token():
    token = request.json.get('token')
    phone_number = request.json.get('phoneNumber')
    if not token or not phone_number:
        return jsonify({'error': 'Missing token or phoneNumber'}), 400

    db[token] = phone_number
    print(f"Token added to APIGateway database: {token} -> {phone_number}")
    return jsonify({'status': 'Token added successfully'}), 200

if __name__ == '__main__':
    app.run(port=5002)