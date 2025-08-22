#!/usr/bin/env python3
"""
Flask API Server for Khmer Products Database
Serves product and manufacturer data from SQLite database
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
# Use absolute path for production deployment
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'khmer_products.db')

# File upload configuration
UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Get database connection with row factory for dict-like access"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Convert sqlite3.Row to dictionary"""
    return dict(row) if row else None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': DATABASE_PATH
    })

# Static file routes
@app.route('/')
def index():
    """Serve the main index.html page"""
    return send_file('index.html')

@app.route('/admin.html')
def admin():
    """Serve the admin panel"""
    return send_file('admin.html')

@app.route('/login.html')
def login():
    """Serve the login page"""
    return send_file('login.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)"""
    if os.path.exists(filename):
        return send_file(filename)
    return "File not found", 404

@app.route('/api/info', methods=['GET'])
def api_info():
    """API information and available endpoints"""
    return jsonify({
        'name': 'Khmer Products API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'GET /api/info': 'API information',
            'GET /api/manufacturers': 'Get all manufacturers',
            'GET /api/products': 'Get all products (supports ?category=, ?manufacturer=, ?search=)',
            'GET /api/products/<id>': 'Get specific product by ID',
            'GET /api/categories': 'Get all categories',
            'GET /api/stats': 'Get database statistics',
            'POST /api/products': 'Add new product',
            'POST /api/manufacturers': 'Add new manufacturer',
            'POST /api/upload/product-image': 'Upload product image file',
            'POST /api/upload/manufacturer-logo': 'Upload manufacturer logo file',
            'DELETE /api/products/<id>': 'Delete product by ID',
            'DELETE /api/manufacturers/<id>': 'Delete manufacturer by ID (if no products reference it)'
        }
    })

@app.route('/api/manufacturers', methods=['GET'])
def get_manufacturers():
    """Get all manufacturers"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM manufacturers ORDER BY name')
        manufacturers = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(manufacturers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get products with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query
        query = '''
            SELECT p.*, m.name as manufacturer_name, m.logo_path as manufacturer_logo
            FROM products p
            LEFT JOIN manufacturers m ON p.manufacturer_id = m.id
        '''
        params = []
        conditions = []
        
        # Add filters
        category = request.args.get('category')
        manufacturer = request.args.get('manufacturer')
        search = request.args.get('search')
        
        if category:
            conditions.append('p.category = ?')
            params.append(category)
            
        if manufacturer:
            conditions.append('m.name = ?')
            params.append(manufacturer)
            
        if search:
            conditions.append('(p.name LIKE ? OR p.description LIKE ?)')
            search_term = f'%{search}%'
            params.extend([search_term, search_term])
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' ORDER BY p.name'
        
        cursor.execute(query, params)
        products = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, m.name as manufacturer_name 
            FROM products p
            LEFT JOIN manufacturers m ON p.manufacturer_id = m.id
            WHERE p.id = ?
        ''', (product_id,))
        
        product = cursor.fetchone()
        conn.close()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        return jsonify(dict_from_row(product)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manufacturers/<int:manufacturer_id>', methods=['GET'])
def get_manufacturer(manufacturer_id):
    """Get a specific manufacturer by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM manufacturers WHERE id = ?', (manufacturer_id,))
        
        manufacturer = cursor.fetchone()
        conn.close()
        
        if not manufacturer:
            return jsonify({'error': 'Manufacturer not found'}), 404
            
        return jsonify(dict_from_row(manufacturer)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories from categories table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY name')
        categories = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['POST'])
def add_category():
    """Add a new category"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Category name is required'}), 400
        
        category_name = data['name'].strip()
        if not category_name:
            return jsonify({'error': 'Category name cannot be empty'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if category already exists
        cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Category already exists'}), 409
        
        # Insert new category
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (category_name,))
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': category_id,
            'name': category_name,
            'message': f'Category "{category_name}" created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category by ID (only if no products use it)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if category exists
        cursor.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
        category = cursor.fetchone()
        if not category:
            conn.close()
            return jsonify({'error': 'Category not found'}), 404
        
        category_name = category[0]
        
        # Check if any products use this category
        cursor.execute('SELECT COUNT(*) FROM products WHERE category = ?', (category_name,))
        product_count = cursor.fetchone()[0]
        
        if product_count > 0:
            conn.close()
            return jsonify({
                'error': f'Cannot delete category "{category_name}" because {product_count} product(s) are using it'
            }), 409
        
        # Delete the category
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Category "{category_name}" deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute('SELECT COUNT(*) FROM products')
        product_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM manufacturers')
        manufacturer_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT category) FROM products')
        category_count = cursor.fetchone()[0]
        
        # Get category breakdown
        cursor.execute('SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC')
        category_stats = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_products': product_count,
            'total_manufacturers': manufacturer_count,
            'total_categories': category_count,
            'category_breakdown': category_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/product-image', methods=['POST'])
def upload_product_image():
    """Upload product image file"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        product_name = request.form.get('product_name', 'product')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            # Create safe filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            safe_product_name = ''.join(c if c.isalnum() else '_' for c in product_name.lower())
            filename = f"{safe_product_name}_{int(datetime.now().timestamp())}.{file_extension}"
            
            # Ensure Product directory exists
            product_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'Product')
            os.makedirs(product_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(product_dir, filename)
            file.save(file_path)
            
            # Return relative path for database storage
            relative_path = f"Product/{filename}"
            return jsonify({
                'message': 'Image uploaded successfully',
                'file_path': relative_path
            }), 201
        else:
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/manufacturer-logo', methods=['POST'])
def upload_manufacturer_logo():
    """Upload manufacturer logo file"""
    try:
        if 'logo' not in request.files:
            return jsonify({'error': 'No logo file provided'}), 400
            
        file = request.files['logo']
        manufacturer_name = request.form.get('manufacturer_name', 'manufacturer')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            # Create safe filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            safe_manufacturer_name = ''.join(c if c.isalnum() else '_' for c in manufacturer_name.lower())
            filename = f"{safe_manufacturer_name}_logo_{int(datetime.now().timestamp())}.{file_extension}"
            
            # Ensure Manufacturers directory exists
            manufacturers_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'Manufacturers')
            os.makedirs(manufacturers_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(manufacturers_dir, filename)
            file.save(file_path)
            
            # Return relative path for database storage
            relative_path = f"Manufacturers/{filename}"
            return jsonify({
                'message': 'Logo uploaded successfully',
                'file_path': relative_path
            }), 201
        else:
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add new product"""
    try:
        data = request.get_json()
        required_fields = ['name', 'category', 'manufacturer_id']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, category, description, image_path, manufacturer_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['category'],
            data.get('description', ''),
            data.get('image_path', ''),
            data['manufacturer_id']
        ))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': product_id, 'message': 'Product added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manufacturers', methods=['POST'])
def add_manufacturer():
    """Add new manufacturer"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO manufacturers (name, description, logo_path, business_name, business_address, business_contact, business_social_network)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data.get('description', ''),
            data.get('logo_path', ''),
            data.get('business_name', ''),
            data.get('business_address', ''),
            data.get('business_contact', ''),
            data.get('business_social_network', '')
        ))
        
        manufacturer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': manufacturer_id, 'message': 'Manufacturer added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT name FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            conn.close()
            return jsonify({'error': 'Product not found'}), 404
            
        # Delete the product
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Product "{product["name"]}" deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        existing_product = cursor.fetchone()
        
        if not existing_product:
            conn.close()
            return jsonify({'error': 'Product not found'}), 404
        
        # Get form data
        name = request.form.get('name')
        category = request.form.get('category')
        manufacturer_id = request.form.get('manufacturer_id')
        description = request.form.get('description', '')
        
        # Validate required fields
        if not all([name, category, manufacturer_id]):
            conn.close()
            return jsonify({'error': 'Name, category, and manufacturer are required'}), 400
        
        # Handle image upload if provided
        image_path = existing_product['image_path']  # Keep existing image by default
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                timestamp = int(datetime.now().timestamp())
                filename = f"{secure_filename(name.lower().replace(' ', '_'))}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"
                
                # Save to Product folder
                product_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'Product')
                os.makedirs(product_folder, exist_ok=True)
                file_path = os.path.join(product_folder, filename)
                file.save(file_path)
                image_path = f"Product/{filename}"
        
        # Update product in database
        cursor.execute('''
            UPDATE products 
            SET name = ?, category = ?, manufacturer_id = ?, description = ?, image_path = ?
            WHERE id = ?
        ''', (name, category, manufacturer_id, description, image_path, product_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Product "{name}" updated successfully',
            'product_id': product_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manufacturers/<int:manufacturer_id>', methods=['PUT'])
def update_manufacturer(manufacturer_id):
    """Update a manufacturer by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if manufacturer exists
        cursor.execute('SELECT * FROM manufacturers WHERE id = ?', (manufacturer_id,))
        existing_manufacturer = cursor.fetchone()
        
        if not existing_manufacturer:
            conn.close()
            return jsonify({'error': 'Manufacturer not found'}), 404
        
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        business_name = request.form.get('business_name', '')
        business_address = request.form.get('business_address', '')
        business_contact = request.form.get('business_contact', '')
        business_social_network = request.form.get('business_social_network', '')
        
        # Validate required fields
        if not name:
            conn.close()
            return jsonify({'error': 'Name is required'}), 400
        
        # Handle logo upload if provided
        logo_path = existing_manufacturer['logo_path']  # Keep existing logo by default
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                timestamp = int(datetime.now().timestamp())
                filename = f"{secure_filename(name.lower().replace(' ', '_'))}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"
                
                # Save to Manufacturers folder
                manufacturer_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'Manufacturers')
                os.makedirs(manufacturer_folder, exist_ok=True)
                file_path = os.path.join(manufacturer_folder, filename)
                file.save(file_path)
                logo_path = f"Manufacturers/{filename}"
        
        # Update manufacturer in database
        cursor.execute('''
            UPDATE manufacturers 
            SET name = ?, description = ?, logo_path = ?, business_name = ?, business_address = ?, business_contact = ?, business_social_network = ?
            WHERE id = ?
        ''', (name, description, logo_path, business_name, business_address, business_contact, business_social_network, manufacturer_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Manufacturer "{name}" updated successfully',
            'manufacturer_id': manufacturer_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manufacturers/<int:manufacturer_id>', methods=['DELETE'])
def delete_manufacturer(manufacturer_id):
    """Delete a manufacturer by ID (only if no products reference it)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if manufacturer exists
        cursor.execute('SELECT name FROM manufacturers WHERE id = ?', (manufacturer_id,))
        manufacturer = cursor.fetchone()
        
        if not manufacturer:
            conn.close()
            return jsonify({'error': 'Manufacturer not found'}), 404
            
        # Check if any products reference this manufacturer
        cursor.execute('SELECT COUNT(*) as count FROM products WHERE manufacturer_id = ?', (manufacturer_id,))
        product_count = cursor.fetchone()['count']
        
        if product_count > 0:
            conn.close()
            return jsonify({'error': f'Cannot delete manufacturer. {product_count} products are still associated with this manufacturer.'}), 400
            
        # Delete the manufacturer
        cursor.execute('DELETE FROM manufacturers WHERE id = ?', (manufacturer_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Manufacturer "{manufacturer["name"]}" deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_admin():
    """Authenticate admin user"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400
            
        username = data['username']
        password = data['password']
        
        # Server-side credential validation
        if username == 'cbsdigitaladmin' and password == 'OVMcKPRLJ78sJEC':
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': username
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Main execution block removed for production deployment
# Use app.py or gunicorn to run the application