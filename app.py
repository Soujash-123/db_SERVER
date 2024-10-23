from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import threading
import os
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from functools import wraps
import secrets

app = Flask(__name__)

# Configuration
class Config:
    # Generate a random secret key on startup
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DATABASE = os.environ.get('DATABASE_PATH', 'your_database.db')
    API_KEY = os.environ.get('API_KEY') or secrets.token_hex(16)
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

app.config.from_object(Config)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security middleware
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == app.config['API_KEY']:
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated

def get_db():
    """Create a database connection with proper timeout and isolation level"""
    db = sqlite3.connect(
        app.config['DATABASE'],
        timeout=20,
        isolation_level='EXCLUSIVE'
    )
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize the database with a sample table"""
    try:
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            db.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    finally:
        db.close()

# Error handling
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"An error occurred: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# API endpoints with security
@app.route('/data', methods=['GET'])
@require_api_key
def get_data():
    """Retrieve all data from the database"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM data')
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}")
        raise
    finally:
        db.close()

@app.route('/data', methods=['POST'])
@require_api_key
def add_data():
    """Add new data to the database"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    value = request.json.get('value')
    if not value:
        return jsonify({"error": "Value is required"}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('INSERT INTO data (value) VALUES (?)', (value,))
        db.commit()
        return jsonify({"message": "Data added successfully"}), 201
    except Exception as e:
        logger.error(f"Error adding data: {str(e)}")
        raise
    finally:
        db.close()

@app.route('/data/<int:id>', methods=['PUT'])
@require_api_key
def update_data(id):
    """Update existing data in the database"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    value = request.json.get('value')
    if not value:
        return jsonify({"error": "Value is required"}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('UPDATE data SET value = ? WHERE id = ?', (value, id))
        db.commit()
        return jsonify({"message": "Data updated successfully"})
    except Exception as e:
        logger.error(f"Error updating data: {str(e)}")
        raise
    finally:
        db.close()

@app.route('/data/<int:id>', methods=['DELETE'])
@require_api_key
def delete_data(id):
    """Delete data from the database"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM data WHERE id = ?', (id,))
        db.commit()
        return jsonify({"message": "Data deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Print the API key for initial setup
    logger.info(f"API Key: {app.config['API_KEY']}")
    
    # Run the Flask server
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=False  # Set to False for production
    )
