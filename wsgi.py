"""WSGI entrypoint for production servers (gunicorn / waitress).
Usage example:
  gunicorn -w 4 -k gthread -b 0.0.0.0:8000 wsgi:app
"""
import os
from app import app

# Optionally switch config based on ENV
config_name = os.getenv('FLASK_CONFIG', 'production')
# app is already created via import; if you refactor to factory, adapt accordingly.

if __name__ == '__main__':
    # Fallback manual run
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
