# app/config.py
import os
from config_loader import load_config

class Config:
    # Load configurations from YAML files
    app_config = load_config('config/app_config.yaml')
    azure_config = load_config('config/azure_config.yaml')

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', app_config['parameters']['secret_key'])
    SESSION_COOKIE_NAME = app_config['parameters']['session_cookie_name']
    MAX_CONTENT_LENGTH = app_config['parameters'].get('max_content_length')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'csv'}

    # Azure configuration
    AZURE_ENDPOINT = azure_config['azure']['endpoint']
    AZURE_API_KEY = os.getenv('AZURE_API_KEY', azure_config['azure']['api_key'])
    AZURE_API_VERSION = azure_config['azure']['api_version']
    AZURE_MODEL = azure_config['azure']['model']
    INSTRUCTIONS = azure_config['instructions']
    VECTOR_STORE_IDS = azure_config['vector_store_ids']

    # Server configuration
    ENVIRONMENT = os.getenv('FLASK_ENV', 'production')
    SERVER_ADDRESS = app_config['servers'][ENVIRONMENT]['address']
    SERVER_PORT = app_config['servers'][ENVIRONMENT]['port']
    DEBUG = app_config['parameters']['debug_mode']
