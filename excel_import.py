#!/usr/bin/env python3
"""
Excel Import Script for Khmer Products Database
Imports manufacturers and products from Excel files into the SQLite database.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

def import_manufacturers_from_excel(excel_file, db_path='khmer_products.db'):
    """
    Import manufacturers from Excel file to database.
    
    Excel file should have columns:
    - name (required)
    - description
    - logo_path
    - business_name
    - business_address
    - business_contact
    - business_social_network
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, sheet_name='Manufacturers')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert manufacturers
        inserted_count = 0
        for index, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO manufacturers 
                    (name, description, logo_path, business_name, business_address, business_contact, business_social_network)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('name', ''),
                    row.get('description', ''),
                    row.get('logo_path', ''),
                    row.get('business_name', ''),
                    row.get('business_address', ''),
                    row.get('business_contact', ''),
                    row.get('business_social_network', '')
                ))
                inserted_count += 1
            except sqlite3.IntegrityError as e:
                print(f"Skipping duplicate manufacturer: {row.get('name', 'Unknown')} - {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Successfully imported {inserted_count} manufacturers from {excel_file}")
        return True
        
    except Exception as e:
        print(f"Error importing manufacturers: {e}")
        return False

def import_categories_from_excel(excel_file, db_path='khmer_products.db'):
    """
    Import categories from Excel file to database.
    
    Excel file should have a 'Categories' sheet with column:
    - name (required)
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, sheet_name='Categories')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create categories table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert categories
        inserted_count = 0
        for index, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO categories (name)
                    VALUES (?)
                """, (row.get('name', ''),))
                inserted_count += 1
            except sqlite3.IntegrityError as e:
                print(f"Skipping duplicate category: {row.get('name', 'Unknown')} - {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Successfully imported {inserted_count} categories from {excel_file}")
        return True
        
    except Exception as e:
        print(f"Error importing categories: {e}")
        return False

def import_products_from_excel(excel_file, db_path='khmer_products.db'):
    """
    Import products from Excel file to database.
    
    Excel file should have columns:
    - name (required)
    - category (required)
    - description
    - manufacturer_name (required - must match existing manufacturer)
    - image_path
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, sheet_name='Products')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get manufacturer mapping
        cursor.execute("SELECT id, name FROM manufacturers")
        manufacturer_map = {name: id for id, name in cursor.fetchall()}
        
        # Insert products
        inserted_count = 0
        for index, row in df.iterrows():
            manufacturer_name = row.get('manufacturer_name', '')
            manufacturer_id = manufacturer_map.get(manufacturer_name)
            product_name = row.get('name', '')
            
            if not manufacturer_id:
                print(f"Skipping product '{product_name}' - manufacturer '{manufacturer_name}' not found")
                continue
            
            # Check if product already exists with same name and manufacturer
            cursor.execute("""
                SELECT id FROM products 
                WHERE name = ? AND manufacturer_id = ?
            """, (product_name, manufacturer_id))
            
            existing_product = cursor.fetchone()
            if existing_product:
                print(f"Skipping duplicate product: '{product_name}' from manufacturer '{manufacturer_name}' already exists")
                continue
                
            try:
                cursor.execute("""
                    INSERT INTO products 
                    (name, category, description, manufacturer_id, image_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    product_name,
                    row.get('category', ''),
                    row.get('description', ''),
                    manufacturer_id,
                    row.get('image_path', '')
                ))
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting product '{product_name}': {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Successfully imported {inserted_count} products from {excel_file}")
        return True
        
    except Exception as e:
        print(f"Error importing products: {e}")
        return False

def create_sample_excel_template(filename='sample_import_template.xlsx'):
    """
    Create a sample Excel template with the correct structure.
    """
    try:
        # Sample manufacturers data
        manufacturers_data = {
            'name': ['ABC Company', 'XYZ Corporation', 'Local Brand'],
            'description': ['Leading food manufacturer', 'Technology solutions provider', 'Traditional Khmer products'],
            'logo_path': ['ABC/logo.jpg', 'XYZ/logo.png', 'LocalBrand/logo.jpg'],
            'business_name': ['ABC Food Industries Ltd.', 'XYZ Tech Corp.', 'Local Brand Co.'],
            'business_address': ['123 Main St, Phnom Penh', '456 Tech Ave, Siem Reap', '789 Local Rd, Battambang'],
            'business_contact': ['+855 12 345 678', '+855 98 765 432', '+855 11 222 333'],
            'business_social_network': ['facebook.com/abc', 'linkedin.com/xyz', 'instagram.com/localbrand']
        }
        
        # Sample categories data
        categories_data = {
            'name': [
                'Food & Beverages',
                'Electronics',
                'Clothing & Textiles',
                'Home & Garden',
                'Health & Beauty',
                'Automotive',
                'Sports & Recreation',
                'Books & Media',
                'Toys & Games',
                'Industrial & Manufacturing'
            ]
        }
        
        # Sample products data
        products_data = {
            'name': ['Premium Rice', 'Smart Phone', 'Traditional Sauce', 'Organic Tea'],
            'category': ['Food & Beverages', 'Electronics', 'Food & Beverages', 'Food & Beverages'],
            'description': ['High quality jasmine rice', 'Latest smartphone model', 'Authentic Khmer fish sauce', 'Organic green tea'],
            'manufacturer_name': ['ABC Company', 'XYZ Corporation', 'Local Brand', 'Local Brand'],
            'image_path': ['ABC/rice.jpg', 'XYZ/phone.png', 'LocalBrand/sauce.jpg', 'LocalBrand/tea.jpg']
        }
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            pd.DataFrame(manufacturers_data).to_excel(writer, sheet_name='Manufacturers', index=False)
            pd.DataFrame(categories_data).to_excel(writer, sheet_name='Categories', index=False)
            pd.DataFrame(products_data).to_excel(writer, sheet_name='Products', index=False)
        
        print(f"Sample Excel template created: {filename}")
        print("\nTemplate structure:")
        print("- Sheet 'Manufacturers': name, description, logo_path, business_name, business_address, business_contact, business_social_network")
        print("- Sheet 'Categories': name (list of available product categories)")
        print("- Sheet 'Products': name, category, description, manufacturer_name, image_path")
        return True
        
    except Exception as e:
        print(f"Error creating template: {e}")
        return False

def main():
    """
    Main function to demonstrate usage.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python excel_import.py create_template    # Create sample Excel template")
        print("  python excel_import.py import <file.xlsx>  # Import from Excel file")
        return
    
    command = sys.argv[1]
    
    if command == 'create_template':
        create_sample_excel_template()
    elif command == 'import' and len(sys.argv) > 2:
        excel_file = sys.argv[2]
        if not os.path.exists(excel_file):
            print(f"File not found: {excel_file}")
            return
        
        print(f"Importing from {excel_file}...")
        
        # Import in order: categories, manufacturers, then products
        success1 = import_categories_from_excel(excel_file)
        success2 = import_manufacturers_from_excel(excel_file)
        success3 = import_products_from_excel(excel_file)
        
        if success1 and success2 and success3:
            print("\nImport completed successfully!")
        else:
            print("\nImport completed with some errors. Check the output above.")
    else:
        print("Invalid command. Use 'create_template' or 'import <file.xlsx>'")

if __name__ == '__main__':
    main()