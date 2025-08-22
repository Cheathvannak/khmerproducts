#!/usr/bin/env python3
"""
Khmer Products Database Examples
Demonstrates various ways to query and interact with the SQLite database.
"""

import sqlite3
import json
from datetime import datetime

class KhmerProductsDB:
    """
    A class to interact with the Khmer Products database.
    """
    
    def __init__(self, db_path='khmer_products.db'):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        return self.conn
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # ==================== READ OPERATIONS ====================
    
    def get_all_manufacturers(self):
        """Get all manufacturers."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM manufacturers ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_products(self):
        """Get all products with manufacturer details."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products_with_manufacturers ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_category(self, category):
        """Get all products in a specific category."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products_with_manufacturers 
            WHERE category = ? 
            ORDER BY name
        """, (category,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_manufacturer(self, manufacturer_name):
        """Get all products from a specific manufacturer."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products_with_manufacturers 
            WHERE manufacturer_name = ? 
            ORDER BY name
        """, (manufacturer_name,))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_products(self, search_term):
        """Search products by name, description, or category."""
        cursor = self.conn.cursor()
        search_pattern = f"%{search_term}%"
        cursor.execute("""
            SELECT * FROM products_with_manufacturers 
            WHERE name LIKE ? 
               OR description LIKE ? 
               OR category LIKE ?
               OR manufacturer_name LIKE ?
            ORDER BY name
        """, (search_pattern, search_pattern, search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_category_stats(self):
        """Get statistics for each category."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM category_stats")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_manufacturer_stats(self):
        """Get statistics for each manufacturer."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM manufacturer_stats")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_categories(self):
        """Get all categories."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        return [row[0] for row in cursor.fetchall()]
    
    # ==================== WRITE OPERATIONS ====================
    
    def add_manufacturer(self, name, description=None, logo_path=None):
        """Add a new manufacturer."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO manufacturers (name, description, logo_path) 
                VALUES (?, ?, ?)
            """, (name, description, logo_path))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Manufacturer '{name}' already exists")
    
    def add_product(self, name, category, description=None, manufacturer_name=None, image_path=None):
        """Add a new product."""
        cursor = self.conn.cursor()
        
        # Get manufacturer ID if manufacturer_name is provided
        manufacturer_id = None
        if manufacturer_name:
            cursor.execute("SELECT id FROM manufacturers WHERE name = ?", (manufacturer_name,))
            result = cursor.fetchone()
            if result:
                manufacturer_id = result[0]
            else:
                raise ValueError(f"Manufacturer '{manufacturer_name}' not found")
        
        cursor.execute("""
            INSERT INTO products (name, category, description, manufacturer_id, image_path) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, description, manufacturer_id, image_path))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_product(self, product_id, **kwargs):
        """Update a product with the given fields."""
        cursor = self.conn.cursor()
        
        # Handle manufacturer_name to manufacturer_id conversion
        if 'manufacturer_name' in kwargs:
            manufacturer_name = kwargs.pop('manufacturer_name')
            cursor.execute("SELECT id FROM manufacturers WHERE name = ?", (manufacturer_name,))
            result = cursor.fetchone()
            if result:
                kwargs['manufacturer_id'] = result[0]
            else:
                raise ValueError(f"Manufacturer '{manufacturer_name}' not found")
        
        # Build dynamic update query
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        
        cursor.execute(f"""
            UPDATE products 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_product(self, product_id):
        """Delete a product."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_manufacturer(self, manufacturer_id):
        """Delete a manufacturer (will fail if products exist)."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM manufacturers WHERE id = ?", (manufacturer_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            raise ValueError("Cannot delete manufacturer with existing products")
    
    # ==================== UTILITY METHODS ====================
    
    def export_to_json(self, filename='khmer_products_export.json'):
        """Export all data to JSON format."""
        data = {
            'manufacturers': self.get_all_manufacturers(),
            'products': self.get_all_products(),
            'categories': self.get_all_categories(),
            'export_date': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename

def demonstrate_queries():
    """
    Demonstrate various database queries.
    """
    print("Khmer Products Database Examples")
    print("=" * 50)
    
    with KhmerProductsDB() as db:
        # 1. Get all manufacturers
        print("\n1. All Manufacturers:")
        manufacturers = db.get_all_manufacturers()
        for manufacturer in manufacturers:
            print(f"   - {manufacturer['name']}: {manufacturer['description']}")
        
        # 2. Get products by category
        print("\n2. Products in 'Condiments & Sauces' category:")
        condiments = db.get_products_by_category('Condiments & Sauces')
        for product in condiments:
            print(f"   - {product['name']} by {product['manufacturer_name']}")
        
        # 3. Get products by manufacturer
        print("\n3. Products by CamboChef:")
        cambochef_products = db.get_products_by_manufacturer('CamboChef')
        for product in cambochef_products:
            print(f"   - {product['name']} ({product['category']})")
        
        # 4. Search products
        print("\n4. Search results for 'milk':")
        milk_products = db.search_products('milk')
        for product in milk_products:
            print(f"   - {product['name']} by {product['manufacturer_name']}")
        
        # 5. Category statistics
        print("\n5. Category Statistics:")
        stats = db.get_category_stats()
        for stat in stats:
            print(f"   - {stat['category']}: {stat['product_count']} products, {stat['manufacturer_count']} manufacturers")
        
        # 6. Manufacturer statistics
        print("\n6. Manufacturer Statistics:")
        manufacturer_stats = db.get_manufacturer_stats()
        for stat in manufacturer_stats:
            print(f"   - {stat['manufacturer_name']}: {stat['product_count']} products in {stat['category_count']} categories")

def demonstrate_crud_operations():
    """
    Demonstrate Create, Read, Update, Delete operations.
    """
    print("\nCRUD Operations Demo")
    print("=" * 30)
    
    with KhmerProductsDB() as db:
        # CREATE: Add a new manufacturer
        print("\n1. Adding new manufacturer 'Test Company'...")
        try:
            manufacturer_id = db.add_manufacturer(
                name="Test Company",
                description="A test company for demonstration",
                logo_path="test/logo.png"
            )
            print(f"   Added manufacturer with ID: {manufacturer_id}")
        except ValueError as e:
            print(f"   Error: {e}")
        
        # CREATE: Add a new product
        print("\n2. Adding new product 'Test Product'...")
        try:
            product_id = db.add_product(
                name="Test Product",
                category="Electronics",
                description="A test product",
                manufacturer_name="Test Company",
                image_path="test/product.jpg"
            )
            print(f"   Added product with ID: {product_id}")
        except ValueError as e:
            print(f"   Error: {e}")
        
        # READ: Get the new product
        print("\n3. Reading the new product...")
        test_products = db.search_products('Test Product')
        if test_products:
            product = test_products[0]
            print(f"   Found: {product['name']} by {product['manufacturer_name']}")
        
        # UPDATE: Update the product
        print("\n4. Updating the product description...")
        if 'product_id' in locals():
            success = db.update_product(
                product_id,
                description="Updated test product description",
                category="Computers"
            )
            print(f"   Update {'successful' if success else 'failed'}")
        
        # DELETE: Remove the test data
        print("\n5. Cleaning up test data...")
        if 'product_id' in locals():
            db.delete_product(product_id)
            print("   Deleted test product")
        
        if 'manufacturer_id' in locals():
            try:
                db.delete_manufacturer(manufacturer_id)
                print("   Deleted test manufacturer")
            except ValueError as e:
                print(f"   Error deleting manufacturer: {e}")

def export_data_example():
    """
    Demonstrate data export functionality.
    """
    print("\nData Export Example")
    print("=" * 25)
    
    with KhmerProductsDB() as db:
        filename = db.export_to_json('khmer_products_backup.json')
        print(f"Data exported to: {filename}")
        
        # Show a sample of the exported data
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\nExported data contains:")
        print(f"   - {len(data['manufacturers'])} manufacturers")
        print(f"   - {len(data['products'])} products")
        print(f"   - {len(data['categories'])} categories")
        print(f"   - Export date: {data['export_date']}")

def main():
    """
    Main function to run all examples.
    """
    try:
        # Check if database exists
        import os
        if not os.path.exists('khmer_products.db'):
            print("Database not found. Please run 'python create_database.py' first.")
            return
        
        # Run demonstrations
        demonstrate_queries()
        demonstrate_crud_operations()
        export_data_example()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("You can now use these patterns in your own applications.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()