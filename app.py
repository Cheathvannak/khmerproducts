#!/usr/bin/env python3
"""
Main entry point for localhost development
Imports the Flask app from api_server.py
"""

from api_server import app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)