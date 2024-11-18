# app/__init__.py
from flask import Flask
from openai import AzureOpenAI
from app.config import Config
from app.logging_config import configure_logging
from app.utils import get_user_email, allowed_file

# Initialize Flask app and configuration
app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
configure_logging(app)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=app.config['AZURE_ENDPOINT'],
    api_key=app.config['AZURE_API_KEY'],
    api_version=app.config['AZURE_API_VERSION']
)

# Configure Assistant
assistant = client.beta.assistants.create(
    instructions=app.config['INSTRUCTIONS'],
    model=app.config['AZURE_MODEL'],
    tools=[{"type": "file_search"}],
)
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": app.config['VECTOR_STORE_IDS']}},
)

# Import routes after initializing components to avoid circular imports
from app import routes
