#!/usr/bin/env python3
"""
Khmer Products Database Creator
Creates and populates a SQLite database with manufacturers and products data.
"""

import sqlite3
import os
import json
from datetime import datetime

def create_database(db_path='khmer_products.db'):
    """
    Create the SQLite database with manufacturers and products tables.
    """
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create new database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create manufacturers table
    cursor.execute('''
        CREATE TABLE manufacturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            logo_path TEXT,
            business_name TEXT,
            business_address TEXT,
            business_contact TEXT,
            business_social_network TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            manufacturer_id INTEGER,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id)
        )
    ''')
    
    # Create categories table for better normalization
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX idx_products_category ON products(category)')
    cursor.execute('CREATE INDEX idx_products_manufacturer ON products(manufacturer_id)')
    cursor.execute('CREATE INDEX idx_products_name ON products(name)')
    
    print("Database schema created successfully!")
    return conn, cursor

def populate_database(conn, cursor):
    """
    Populate the database with the existing data from the JavaScript file.
    """
    
    # Insert manufacturers data
    manufacturers_data = [
        (1, 'CamboChef', 'CamboChef', 'CamboChef/cambochef_logo.jpg'),
        (2, 'Kirisu', 'Kirisu Farm', 'Kirisu/kirisu_logo.png'),
        (3, 'Khmer Beverages', 'Khmer Beverages', 'KhmerBeverages/KhmerBeverages_Logo.png')
    ]
    
    cursor.executemany('''
        INSERT INTO manufacturers (id, name, description, logo_path) 
        VALUES (?, ?, ?, ?)
    ''', manufacturers_data)
    
    # Insert categories data
    categories_data = [
        ('Condiments & Sauces',),
        ('Food & Beverages',),
        ('Household',),
        ('Dairy',),
        ('Coffee',),
        ('Gasoline Station',),

    ]
    
    cursor.executemany('INSERT INTO categories (name) VALUES (?)', categories_data)
    
    # Insert products data
    products_data = [
        (1, 'Fish Sauce', 'Condiments & Sauces', 'CamboChef', 1, 'CamboChef/cambochef_fishsauce.jpg'),
        (2, 'Romduol Cooking Oil', 'Condiments & Sauces', 'CamboChef', 1, 'CamboChef/cambochef_cookingoil.jpg'),
        (3, 'Premium Oyster Sauce', 'Condiments & Sauces', 'CamboChef', 1, 'CamboChef/cambochef_oystersauce.jpg'),
        (4, 'Premium Anchovy Sauce', 'Condiments & Sauces', 'CamboChef', 1, 'CamboChef/cambochef_premiumanchovysauce.jpg'),
        (5, 'Soy Sauce', 'Condiments & Sauces', 'CamboChef', 1, 'CamboChef/cambochef_soysauce.jpg'),
        (6, 'Dish Soap', 'Household', 'CamboChef', 1, 'CamboChef/cambochef_dishsoap.jpg'),
        (7, 'Fresh Milk', 'Dairy', 'Kirisu Farm', 2, 'Kirisu/Kirisu_FreshMilk.png'),
        (8, 'Cambodia Premium Water', 'Food & Beverages', 'Khmer Beverages', 3, 'KhmerBeverages/Cambodia_Premium_Water.png'),
        (9, 'Wurkz Energy Drink', 'Food & Beverages', 'Khmer Beverages', 3, 'KhmerBeverages/Wurkz.png'),
        (10, 'Barista Milk', 'Dairy', 'Kirisu Farm', 2, 'Kirisu/Kirisu_BaristaMilk.png'),
        (11, 'Cambodia Premium Beer', 'Food & Beverages', 'Khmer Beverages', 3, 'KhmerBeverages/Cambodia_Premium_Beer.png')

    ]
    
    cursor.executemany('''
        INSERT INTO products (id, name, category, description, manufacturer_id, image_path) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', products_data)
    
    # Commit the changes
    conn.commit()
    print(f"Database populated with {len(manufacturers_data)} manufacturers and {len(products_data)} products!")

def create_views(conn, cursor):
    """
    Create useful views for common queries.
    """
    
    # View for products with manufacturer details
    cursor.execute('''
        CREATE VIEW products_with_manufacturers AS
        SELECT 
            p.id,
            p.name,
            p.category,
            p.description,
            p.image_path,
            m.name as manufacturer_name,
            m.description as manufacturer_description,
            m.logo_path as manufacturer_logo,
            p.created_at,
            p.updated_at
        FROM products p
        LEFT JOIN manufacturers m ON p.manufacturer_id = m.id
    ''')
    
    # View for category statistics
    cursor.execute('''
        CREATE VIEW category_stats AS
        SELECT 
            category,
            COUNT(*) as product_count,
            COUNT(DISTINCT manufacturer_id) as manufacturer_count
        FROM products
        GROUP BY category
        ORDER BY product_count DESC
    ''')
    
    # View for manufacturer statistics
    cursor.execute('''
        CREATE VIEW manufacturer_stats AS
        SELECT 
            m.name as manufacturer_name,
            m.description,
            COUNT(p.id) as product_count,
            COUNT(DISTINCT p.category) as category_count
        FROM manufacturers m
        LEFT JOIN products p ON m.id = p.manufacturer_id
        GROUP BY m.id, m.name, m.description
        ORDER BY product_count DESC
    ''')
    
    conn.commit()
    print("Database views created successfully!")

def main():
    """
    Main function to create and populate the database.
    """
    print("Creating Khmer Products SQLite Database...")
    print("=" * 50)
    
    # Create database and tables
    conn, cursor = create_database()
    
    # Populate with data
    populate_database(conn, cursor)
    
    # Create views
    create_views(conn, cursor)
    
    # Display some statistics
    print("\nDatabase Statistics:")
    print("-" * 30)
    
    cursor.execute("SELECT COUNT(*) FROM manufacturers")
    manufacturer_count = cursor.fetchone()[0]
    print(f"Manufacturers: {manufacturer_count}")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    print(f"Products: {product_count}")
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    category_count = cursor.fetchone()[0]
    print(f"Categories: {category_count}")
    
    print("\nCategory breakdown:")
    cursor.execute("SELECT * FROM category_stats")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} products, {row[2]} manufacturers")
    
    # Close connection
    conn.close()
    
    print(f"\nDatabase created successfully: khmer_products.db")
    print("You can now use this database with any SQLite client or Python script.")

if __name__ == "__main__":
    main()