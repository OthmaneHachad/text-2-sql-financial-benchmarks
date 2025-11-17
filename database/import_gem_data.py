"""
GEM Data Import Script
Imports World Bank Global Economic Monitor data from multiple Excel files into SQLite database.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import re

def parse_indicator_from_filename(filename):
    """
    Extract indicator information from filename.
    
    Examples:
        'GDP at market prices, current US$, millions, seas. adj..xlsx'
        -> name: 'GDP at market prices', unit: 'current US$, millions', seasonal_adj: True
    """
    # Remove .xlsx extension
    name = filename.replace('.xlsx', '')
    
    # Determine if seasonally adjusted
    seasonal_adj = 'seas. adj.' in name.lower() or 'seas adj' in name.lower()
    
    # Clean up the name
    name = name.replace(', seas. adj.', '').replace(', not seas. adj.', '')
    name = name.replace('..', '.')
    
    # Try to extract unit information
    parts = [p.strip() for p in name.split(',')]
    indicator_name = parts[0] if parts else name
    unit = ', '.join(parts[1:]) if len(parts) > 1 else None
    
    return indicator_name, unit, seasonal_adj

def import_gem_file(excel_path, conn, cursor, country_lookup, indicator_lookup):
    """
    Import a single GEM Excel file.
    
    Args:
        excel_path: Path to the Excel file
        conn: Database connection
        cursor: Database cursor
        country_lookup: Dictionary mapping country names to IDs
        indicator_lookup: Dictionary mapping indicator codes to IDs
        
    Returns:
        Number of observations imported
    """
    # Parse indicator info from filename
    filename = Path(excel_path).name
    indicator_name, unit, seasonal_adj = parse_indicator_from_filename(filename)
    
    # Create a unique indicator code from the filename
    indicator_code = f"GEM_{filename.replace('.xlsx', '').replace(' ', '_').replace(',', '')[:50]}"
    
    # Insert indicator if it doesn't exist
    cursor.execute('''
        INSERT OR IGNORE INTO indicators (indicator_code, indicator_name, source, unit)
        VALUES (?, ?, 'GEM', ?)
    ''', (indicator_code, indicator_name, unit))
    conn.commit()
    
    # Get indicator ID
    cursor.execute('SELECT indicator_id FROM indicators WHERE indicator_code = ?', (indicator_code,))
    indicator_id = cursor.fetchone()[0]
    
    # Read Excel file
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"  ⚠️  Error reading {filename}: {e}")
        return 0
    
    # First column should be years, rest are countries
    if df.empty or len(df.columns) < 2:
        print(f"  ⚠️  Skipping {filename}: insufficient data")
        return 0
    
    # Get year column (first column)
    year_col = df.columns[0]
    years = df[year_col].dropna()
    
    # Get country columns (all except first)
    country_cols = df.columns[1:]
    
    observations = []
    
    for idx, year in enumerate(years):
        try:
            year_int = int(float(year))
            
            # Skip if year is outside our range
            if year_int < 1972 or year_int > 2024:
                continue
                
            for country_col in country_cols:
                value = df.iloc[idx][country_col]
                
                # Only insert if we have a valid value
                if pd.notna(value):
                    country_id = country_lookup.get(country_col)
                    
                    # If country not in our database, add it
                    if country_id is None:
                        cursor.execute('INSERT OR IGNORE INTO countries (country_name) VALUES (?)', 
                                     (country_col,))
                        conn.commit()
                        cursor.execute('SELECT country_id FROM countries WHERE country_name = ?', 
                                     (country_col,))
                        country_id = cursor.fetchone()[0]
                        country_lookup[country_col] = country_id
                    
                    observations.append((
                        country_id,
                        year_int,
                        indicator_id,
                        float(value),
                        seasonal_adj
                    ))
        except (ValueError, TypeError):
            continue
    
    # Batch insert observations
    if observations:
        cursor.executemany('''
            INSERT INTO gem_observations 
            (country_id, year, indicator_id, value, seasonal_adjustment)
            VALUES (?, ?, ?, ?, ?)
        ''', observations)
        conn.commit()
    
    return len(observations)

def import_gem_data(gem_directory, db_path='economic_data.db'):
    """
    Import all GEM Excel files from a directory.
    
    Args:
        gem_directory: Path to directory containing GEM Excel files
        db_path: Path to the SQLite database
    """
    print("=" * 80)
    print("World Bank GEM Data Import")
    print("=" * 80)
    
    gem_dir = Path(gem_directory)
    if not gem_dir.exists():
        raise FileNotFoundError(f"GEM directory not found: {gem_directory}")
    
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Run database_setup.py first.")
    
    # Find all Excel files
    excel_files = list(gem_dir.glob("*.xlsx"))
    
    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in {gem_directory}")
    
    print(f"\nFound {len(excel_files)} Excel files to process")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get country lookup
    country_lookup = {name: id for id, name in 
                     cursor.execute('SELECT country_id, country_name FROM countries').fetchall()}
    indicator_lookup = {code: id for id, code in 
                       cursor.execute('SELECT indicator_id, indicator_code FROM indicators WHERE source="GEM"').fetchall()}
    
    # Process each Excel file
    print("\n💾 Importing GEM data files...")
    total_observations = 0
    
    for excel_file in tqdm(excel_files, desc="Processing files"):
        obs_count = import_gem_file(excel_file, conn, cursor, country_lookup, indicator_lookup)
        total_observations += obs_count
    
    # Print summary
    cursor.execute('SELECT COUNT(DISTINCT country_id) FROM gem_observations')
    country_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT indicator_id) FROM gem_observations')
    indicator_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT year) FROM gem_observations')
    year_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 80)
    print("✅ GEM Import Complete!")
    print("=" * 80)
    print(f"Files processed:     {len(excel_files):,}")
    print(f"Countries:           {country_count:,}")
    print(f"Indicators:          {indicator_count:,}")
    print(f"Years:               {year_count:,}")
    print(f"Observations:        {total_observations:,}")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    # Update this path to your actual GEM data directory
    gem_dir = "Gem Data Extraction"
    
    if Path(gem_dir).exists():
        import_gem_data(gem_dir)
    else:
        print(f"Error: Could not find directory {gem_dir}")
        print("Please update the gem_dir path in this script.")
