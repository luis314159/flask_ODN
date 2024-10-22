# app.py
import logging
from flask import Flask, request, jsonify, render_template
from openai import AzureOpenAI
from config_loader import load_config
import time
import os

# Cargar configuración de la aplicación
app_config = load_config('app_config.yaml')

# Cargar configuración de Azure
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


# Azure parameters
endpoint = azure_config['azure']['endpoint']
api_key = azure_config['azure']['api_key']
api_version = azure_config['azure']['api_version']
model = azure_config['azure']['model']
instructions = azure_config['instructions']
vector_store_ids = azure_config['vector_store_ids']

# Configurar el logger de la aplicación
app.logger.setLevel(logging.INFO)

# Evitar que los logs se dupliquen
app.logger.propagate = False

# Eliminar handlers existentes (si los hay)
if app.logger.hasHandlers():
    app.logger.handlers.clear()



# Handler para escribir en archivo
file_handler = logging.FileHandler('chat_responses.log', mode='a')
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)
app.logger.addHandler(file_handler)
app.logger.info('Logger files handler inicializado correctamente.')

# Handler para mostrar los logs en la consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
app.logger.addHandler(console_handler)
app.logger.info('Logger stream handler inicializado correctamente.')

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

assistant = client.beta.assistants.create(
    instructions="",
    model=model,
    tools=[{"type": "file_search"}],
)
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": vector_store_ids}},
)

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Acceder al contenido de los mensajes
        response_message = None
        for msg in messages.data:
            if msg.role == "assistant":
                response_message = msg.content[0].text.value  # Extraer el texto de la respuesta
                break
        
        if response_message:
            app.logger.info(f"Assistant response: {response_message}")
            app.logger.info(f"Assistant full_message: {msg}")
            return jsonify({"response": response_message})
        else:
            return jsonify({"error": "No response from assistant"}), 500
    else:
        return jsonify({"error": "Something went wrong"}), 500


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host=address, port=port, debug=app_config['parameters']['debug_mode'])