# Khmer Products SQLite Database

This directory contains SQLite database scripts for the Khmer Products application. The database stores manufacturers, products, and categories in a normalized structure.

## Files

- `create_database.py` - Creates and populates the SQLite database
- `database_examples.py` - Demonstrates various database operations and queries
- `DATABASE_README.md` - This documentation file
- `khmer_products.db` - The SQLite database file (created after running scripts)

## Database Schema

### Tables

#### `manufacturers`
- `id` (INTEGER PRIMARY KEY) - Unique manufacturer ID
- `name` (TEXT NOT NULL UNIQUE) - Manufacturer name
- `description` (TEXT) - Manufacturer description
- `logo_path` (TEXT) - Path to manufacturer logo
- `created_at` (TIMESTAMP) - Record creation time
- `updated_at` (TIMESTAMP) - Record last update time

#### `products`
- `id` (INTEGER PRIMARY KEY) - Unique product ID
- `name` (TEXT NOT NULL) - Product name
- `category` (TEXT NOT NULL) - Product category
- `description` (TEXT) - Product description
- `manufacturer_id` (INTEGER) - Foreign key to manufacturers table
- `image_path` (TEXT) - Path to product image
- `created_at` (TIMESTAMP) - Record creation time
- `updated_at` (TIMESTAMP) - Record last update time

#### `categories`
- `id` (INTEGER PRIMARY KEY) - Unique category ID
- `name` (TEXT NOT NULL UNIQUE) - Category name
- `created_at` (TIMESTAMP) - Record creation time

### Views

#### `products_with_manufacturers`
Joins products with manufacturer details for easy querying.

#### `category_stats`
Provides statistics about products per category.

#### `manufacturer_stats`
Provides statistics about products per manufacturer.

## Quick Start

### 1. Create the Database

```bash
python3 create_database.py
```

This will:
- Create `khmer_products.db` SQLite database
- Create all tables and indexes
- Populate with existing product and manufacturer data
- Create useful views for common queries

### 2. Run Examples

```bash
python3 database_examples.py
```

This will demonstrate:
- Basic queries (get all products, manufacturers, etc.)
- Filtering by category and manufacturer
- Search functionality
- CRUD operations (Create, Read, Update, Delete)
- Data export to JSON

## Usage Examples

### Basic Python Usage

```python
from database_examples import KhmerProductsDB

# Using context manager (recommended)
with KhmerProductsDB() as db:
    # Get all products
    products = db.get_all_products()
    
    # Get products by category
    dairy_products = db.get_products_by_category('Dairy')
    
    # Search products
    results = db.search_products('milk')
    
    # Get manufacturer statistics
    stats = db.get_manufacturer_stats()
```

### Direct SQL Queries

```python
import sqlite3

conn = sqlite3.connect('khmer_products.db')
cursor = conn.cursor()

# Get all CamboChef products
cursor.execute("""
    SELECT p.name, p.category, m.name as manufacturer
    FROM products p
    JOIN manufacturers m ON p.manufacturer_id = m.id
    WHERE m.name = 'CamboChef'
""")

for row in cursor.fetchall():
    print(f"{row[0]} - {row[1]} by {row[2]}")

conn.close()
```

## Common Queries

### Get Products by Category
```sql
SELECT * FROM products_with_manufacturers 
WHERE category = 'Condiments & Sauces' 
ORDER BY name;
```

### Get Products by Manufacturer
```sql
SELECT * FROM products_with_manufacturers 
WHERE manufacturer_name = 'CamboChef' 
ORDER BY name;
```

### Search Products
```sql
SELECT * FROM products_with_manufacturers 
WHERE name LIKE '%milk%' 
   OR description LIKE '%milk%' 
   OR category LIKE '%milk%'
ORDER BY name;
```

### Category Statistics
```sql
SELECT * FROM category_stats;
```

### Manufacturer Statistics
```sql
SELECT * FROM manufacturer_stats;
```

## Adding New Data

### Add a New Manufacturer
```python
with KhmerProductsDB() as db:
    manufacturer_id = db.add_manufacturer(
        name="New Company",
        description="A new manufacturer",
        logo_path="logos/new_company.png"
    )
```

### Add a New Product
```python
with KhmerProductsDB() as db:
    product_id = db.add_product(
        name="New Product",
        category="Electronics",
        description="A new electronic product",
        manufacturer_name="New Company",
        image_path="products/new_product.jpg"
    )
```

### Update a Product
```python
with KhmerProductsDB() as db:
    success = db.update_product(
        product_id=1,
        name="Updated Product Name",
        description="Updated description"
    )
```

## Data Export

Export all data to JSON format:

```python
with KhmerProductsDB() as db:
    filename = db.export_to_json('backup.json')
    print(f"Data exported to {filename}")
```

## Database Tools

### SQLite Command Line
```bash
# Open database in SQLite CLI
sqlite3 khmer_products.db

# Common SQLite commands
.tables          # List all tables
.schema          # Show table schemas
.quit            # Exit SQLite CLI
```

### GUI Tools
- **DB Browser for SQLite** - Free, cross-platform GUI
- **SQLiteStudio** - Feature-rich SQLite manager
- **DBeaver** - Universal database tool

## Integration with Web Application

To integrate this database with your existing web application:

1. **Replace JavaScript arrays** with database queries
2. **Create API endpoints** to serve data from the database
3. **Use the KhmerProductsDB class** in your backend code
4. **Implement caching** for better performance

### Example Flask Integration
```python
from flask import Flask, jsonify
from database_examples import KhmerProductsDB

app = Flask(__name__)

@app.route('/api/products')
def get_products():
    with KhmerProductsDB() as db:
        products = db.get_all_products()
    return jsonify(products)

@app.route('/api/products/category/<category>')
def get_products_by_category(category):
    with KhmerProductsDB() as db:
        products = db.get_products_by_category(category)
    return jsonify(products)
```

## Performance Considerations

- **Indexes** are created on commonly queried columns
- **Views** provide pre-optimized queries for common operations
- **Connection pooling** recommended for high-traffic applications
- **Caching** can be implemented at the application level

## Backup and Maintenance

### Create Backup
```bash
# SQLite backup
sqlite3 khmer_products.db ".backup backup_$(date +%Y%m%d).db"

# Or use the export function
python3 -c "from database_examples import KhmerProductsDB; KhmerProductsDB().export_to_json('backup.json')"
```

### Database Maintenance
```sql
-- Analyze database for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM;
```

## Troubleshooting

### Common Issues

1. **Database locked**: Close all connections before running scripts
2. **Permission denied**: Ensure write permissions in the directory
3. **Module not found**: Install required Python modules

### Reset Database
```bash
# Delete existing database and recreate
rm khmer_products.db
python3 create_database.py
```

## Requirements

- Python 3.6+
- SQLite3 (included with Python)
- No additional dependencies required

## License

This database schema and scripts are part of the Khmer Products application.