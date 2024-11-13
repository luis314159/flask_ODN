# app.py
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from openai import AzureOpenAI
from config_loader import load_config
import time
import os
from ldap3 import Server, Connection, ALL

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


# Asegúrate de agregar estas configuraciones al archivo app_config.yaml
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'xlsx', 'csv'}

def allowed_file(filename):
    allowed_extensions = {'pdf', 'doc', 'docx', 'xlsx', 'csv'}  # Cambia según tus necesidades
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_user_email(username):
    try:
        server = Server('ldap://tu_servidor_ldap', get_info=ALL)
        conn = Connection(server, user='usuario_bind', password='contraseña_bind', auto_bind=True)
        conn.search('dc=tu_dominio,dc=com', f'(sAMAccountName={username})', attributes=['mail'])
        if conn.entries:
            return conn.entries[0]['mail'].value
    except Exception as e:
        app.logger.error(f"Error al obtener el correo electrónico: {e}")
    return None

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                # Subir el archivo y obtener el file_id
                uploaded_file = client.files.create(
                    file=(file.filename, file.read()),  # Leer el contenido del archivo y pasarlo como una tupla (nombre, bytes)
                    purpose='assistants'
                )

                file_id = uploaded_file['id']  # Obtener el ID del archivo subido

                # Asociar el archivo al vector store
                batch_add = client.beta.vector_stores.file_batches.create(
                    vector_store_id=vector_store_ids,  # Reemplaza esto con tu ID de vector store real
                    file_ids=[file_id]
                )

                if batch_add.status == 'succeeded':
                    flash('Files successfully uploaded and added to the vector store')
                else:
                    flash('File uploaded but failed to add to the vector store')
            except Exception as e:
                app.logger.error(f"Error uploading file: {e}")
                flash('Error uploading file')
            return redirect(url_for('upload_file'))
    
    return render_template('upload.html')



@app.route('/')
def index():
    user = request.environ.get('REMOTE_USER')
    if user:
        # Si el nombre de usuario viene con el dominio (DOMINIO\usuario), lo separamos
        username = user.split('\\')[-1]
        # Obtener el correo electrónico del usuario
        email = get_user_email(username)
        return render_template('index.html', username=username, email=email)
    else:
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

@app.route('/get_default_questions')
def get_default_questions():
    questions = [
        "What was the best performing plant today?",
        "Which plant had the lowest efficiency?",
        "Were there any major issues today?",
        "What was the overall scrap rate across all plants?",
        "What was the average cycle time across all lines?",
        "What was the most frequent cause of production delays today?",
        "What was the top bottleneck in production today?"
    ]
    return jsonify(questions)


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000, debug=True)
    from waitress import serve

    app.config['DEBUG'] = app_config['parameters']['debug_mode']
    app.logger.info(f"Starting Waitress server on {address}:{port}")
    # Configurar el logger de la aplicación
    app.logger.setLevel(logging.INFO)
    serve(app, host=address, port=port)

    """
    from waitress import serve
    app.config['DEBUG'] = app_config['parameters']['debug_mode']
    app.logger.info(f"Starting Waitress server on {address}:{port}")
    # Configurar el logger de la aplicación
    app.logger.setLevel(logging.INFO)
    port=3005
    #serve(app, host=address, port=port)
    
    #app.run(host=address, port=port, debug=True)
    app.run(host=address, debug=True)
    """
