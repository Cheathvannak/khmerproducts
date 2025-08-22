#!/usr/bin/env python3
"""
Main entry point for Render deployment
Imports the Flask app from api_server.py
"""

from api_server import app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)