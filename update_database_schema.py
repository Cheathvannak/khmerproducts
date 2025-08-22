#!/usr/bin/env python3
"""
Database Schema Update Script
Adds new business fields to the existing manufacturers table without losing data.
"""

import sqlite3
import os

def update_manufacturers_table(db_path='khmer_products.db'):
    """
    Add new business fields to the manufacturers table.
    """
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the new columns already exist
        cursor.execute("PRAGMA table_info(manufacturers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = [
            'business_name',
            'business_address', 
            'business_contact',
            'business_social_network'
        ]
        
        # Add new columns if they don't exist
        for column in new_columns:
            if column not in columns:
                cursor.execute(f'ALTER TABLE manufacturers ADD COLUMN {column} TEXT')
                print(f"Added column: {column}")
            else:
                print(f"Column {column} already exists")
        
        conn.commit()
        conn.close()
        
        print("Database schema updated successfully!")
        print("All existing data has been preserved.")
        return True
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        return False

if __name__ == '__main__':
    update_manufacturers_table()