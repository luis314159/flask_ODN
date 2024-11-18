# app/routes.py
from flask import request, jsonify, render_template, redirect, url_for, flash
from app import app, client, assistant
from app.utils import allowed_file, get_user_email
import time
from datetime import datetime

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                uploaded_file = client.files.create(
                    file=(file.filename, file.read()),
                    purpose='assistants'
                )
                file_id = uploaded_file['id']

                batch_add = client.beta.vector_stores.file_batches.create(
                    vector_store_id=app.config['VECTOR_STORE_IDS'],
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

from flask import Flask, render_template, request
from datetime import datetime

@app.route('/')
def index():
    user = request.environ.get('REMOTE_USER')
    date = date = datetime(2024, 11, 12)
    data = {'data_date': date.date(), 'today_date': datetime.today().date()}
    
    if user:
        username = user.split('\\')[-1]
        email = get_user_email(username)
        data.update({
            'username': username,
            'email': email
        })
    return render_template('index.html', **data)


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

    max_retries = 10
    retries = 0

    while run.status in ['queued', 'in_progress', 'cancelling'] and retries < max_retries:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        retries += 1

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_message = None
        for msg in messages.data:
            if msg.role == "assistant":
                response_message = msg.content[0].text.value
                break

        if response_message:
            app.logger.info(f"Assistant response: {response_message}")
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
