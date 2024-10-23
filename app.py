# app.py
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
DATABASE = 'your_database.db'

def get_db():
    """Create a database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize the database with a sample table"""
    db = get_db()
    cursor = db.cursor()
    
    # Create a sample table - modify according to your needs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.commit()
    db.close()

# API endpoints
@app.route('/')
def home():
    """Health check endpoint"""
    return "Server is running!"

@app.route('/data', methods=['GET'])
def get_data():
    """Retrieve all data from the database"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM data')
    rows = cursor.fetchall()
    
    data = [dict(row) for row in rows]
    db.close()
    
    return jsonify(data)

@app.route('/data', methods=['POST'])
def add_data():
    """Add new data to the database"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    value = request.json.get('value')
    if not value:
        return jsonify({"error": "Value is required"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('INSERT INTO data (value) VALUES (?)', (value,))
    db.commit()
    db.close()
    
    return jsonify({"message": "Data added successfully"}), 201

@app.route('/data/<int:id>', methods=['PUT'])
def update_data(id):
    """Update existing data in the database"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    value = request.json.get('value')
    if not value:
        return jsonify({"error": "Value is required"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('UPDATE data SET value = ? WHERE id = ?', (value, id))
    db.commit()
    db.close()
    
    return jsonify({"message": "Data updated successfully"})

@app.route('/data/<int:id>', methods=['DELETE'])
def delete_data(id):
    """Delete data from the database"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM data WHERE id = ?', (id,))
    db.commit()
    db.close()
    
    return jsonify({"message": "Data deleted successfully"})

# Initialize database when the app starts
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
