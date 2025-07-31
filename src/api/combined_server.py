#!/usr/bin/env python3
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='kbi_dashboard')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('kbi_dashboard', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('kbi_dashboard', path)

@app.route('/api/companies', methods=['GET'])
@app.route('/api/companies/<uei>', methods=['GET'])
def proxy_companies(uei=None):
    if uei:
        url = f"http://localhost:5000/api/companies/{uei}"
    else:
        url = "http://localhost:5000/api/companies"
    
    try:
        response = requests.get(url)
        return response.json()
    except:
        return jsonify({"error": "Company API not available"}), 500

@app.route('/api/insights/<uei>', methods=['GET'])
def proxy_insights(uei):
    params = request.args.to_dict()
    try:
        response = requests.get(f"http://localhost:5001/api/insights/{uei}", params=params)
        return response.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.system('pip install requests flask flask-cors')
    app.run(host='0.0.0.0', port=8090, debug=False)
