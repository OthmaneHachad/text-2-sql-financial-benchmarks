"""
Database Setup Script
Creates the SQLite database and defines the schema for economic data integration.
"""

import sqlite3
from pathlib import Path

def create_database(db_path='economic_data.db'):
    """
    Create database and all necessary tables.
    
    Args:
        db_path: Path where the SQLite database will be created
    """
    # Remove existing database if it exists
    if Path(db_path).exists():
        print(f"Warning: Database {db_path} already exists. It will be recreated.")
        Path(db_path).unlink()
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating database schema...")
    
    # Create countries table
    cursor.execute('''
        CREATE TABLE countries (
            country_id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_name TEXT UNIQUE NOT NULL,
            region TEXT
        )
    ''')
    print("✓ Created countries table")
    
    # Create time_periods table
    cursor.execute('''
        CREATE TABLE time_periods (
            year INTEGER PRIMARY KEY
        )
    ''')
    print("✓ Created time_periods table")
    
    # Create sectors table (for GFS data)
    cursor.execute('''
        CREATE TABLE sectors (
            sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sector_name TEXT UNIQUE NOT NULL,
            sector_description TEXT
        )
    ''')
    print("✓ Created sectors table")
    
    # Create indicators table
    cursor.execute('''
        CREATE TABLE indicators (
            indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_code TEXT UNIQUE,
            indicator_name TEXT NOT NULL,
            source TEXT CHECK(source IN ('GFS', 'GEM')),
            unit TEXT,
            description TEXT
        )
    ''')
    print("✓ Created indicators table")
    
    # Create GFS observations table
    cursor.execute('''
        CREATE TABLE gfs_observations (
            observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            sector_id INTEGER,
            indicator_id INTEGER NOT NULL,
            value REAL,
            transformation TEXT,
            scale TEXT,
            frequency TEXT,
            FOREIGN KEY (country_id) REFERENCES countries(country_id),
            FOREIGN KEY (year) REFERENCES time_periods(year),
            FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
            FOREIGN KEY (indicator_id) REFERENCES indicators(indicator_id)
        )
    ''')
    print("✓ Created gfs_observations table")
    
    # Create GEM observations table
    cursor.execute('''
        CREATE TABLE gem_observations (
            observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            indicator_id INTEGER NOT NULL,
            value REAL,
            seasonal_adjustment BOOLEAN,
            FOREIGN KEY (country_id) REFERENCES countries(country_id),
            FOREIGN KEY (year) REFERENCES time_periods(year),
            FOREIGN KEY (indicator_id) REFERENCES indicators(indicator_id)
        )
    ''')
    print("✓ Created gem_observations table")
    
    # Create indexes for faster queries
    print("\nCreating indexes...")
    cursor.execute('CREATE INDEX idx_gfs_country_year ON gfs_observations(country_id, year)')
    cursor.execute('CREATE INDEX idx_gfs_indicator ON gfs_observations(indicator_id)')
    cursor.execute('CREATE INDEX idx_gem_country_year ON gem_observations(country_id, year)')
    cursor.execute('CREATE INDEX idx_gem_indicator ON gem_observations(indicator_id)')
    print("✓ Created performance indexes")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database '{db_path}' created successfully!")
    print(f"   Location: {Path(db_path).absolute()}")
    
    return db_path

if __name__ == "__main__":
    create_database()
