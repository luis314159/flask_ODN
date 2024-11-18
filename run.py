# run.py
from app import app
from waitress import serve

if __name__ == '__main__':
    app.logger.info(f"Starting Waitress server on {app.config['SERVER_ADDRESS']}:{app.config['SERVER_PORT']}")
    serve(app, host=app.config['SERVER_ADDRESS'], port=app.config['SERVER_PORT'])
