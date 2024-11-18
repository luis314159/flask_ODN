# app/logging_config.py
import logging

def configure_logging(app):
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler('chat_responses.log', mode='a')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    app.logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    app.logger.addHandler(console_handler)

    app.logger.info('Logger configured successfully.')
