import logging
from config_loader import load_config
from flask import Flask, request, jsonify, render_template
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load application configuration
app_config = load_config('app_config.yaml')

# Load Azure configuration
azure_config = load_config('azure_config.yaml')

app = Flask(__name__)

# Configure Flask
app.config['SECRET_KEY'] = app_config['parameters']['secret_key']
app.config['SESSION_COOKIE_NAME'] = app_config['parameters']['session_cookie_name']
max_content_length = app_config['parameters'].get('max_content_length')
if max_content_length is not None:
    app.config['MAX_CONTENT_LENGTH'] = max_content_length

# Select server
environment = os.getenv('FLASK_ENV', 'production')
server = app_config['servers'][environment]
address = server['address']
port = server['port']


logging.info(f"environment: {environment}")
logging.info(f"server: {server}")
logging.info(f"address: {address}")
logging.info(f"port: {port}")


# Azure parameters
endpoint = azure_config['azure']['endpoint']
api_key = azure_config['azure']['api_key']
api_version = azure_config['azure']['api_version']
model = azure_config['azure']['model']
instructions = azure_config['instructions']
vector_store_ids = azure_config['vector_store_ids']

# Log Azure parameters for verification
logging.info(f"Azure Endpoint: {endpoint}")
logging.info(f"API Key: {api_key}")
logging.info(f"API Version: {api_version}")
logging.info(f"Model: {model}")
logging.info(f"Instructions: {instructions}")
logging.info(f"Vector Store IDs: {vector_store_ids}")


@app.route('/')
def index():

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host=address, port=port, debug=app_config['parameters']['debug_mode'])
