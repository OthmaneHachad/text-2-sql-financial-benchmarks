"""
GFS Data Import Script
Imports IMF Government Finance Statistics data from CSV into the SQLite database.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def import_gfs_data(csv_path, db_path='economic_data.db', chunk_size=1000):
    """
    Import GFS data from CSV into database.
    
    Args:
        csv_path: Path to the GFS CSV file
        db_path: Path to the SQLite database
        chunk_size: Number of rows to process at a time (for memory efficiency)
    """
    print("=" * 80)
    print("IMF GFS Data Import")
    print("=" * 80)
    
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"GFS CSV file not found: {csv_path}")
    
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Run database_setup.py first.")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total row count for progress bar
    print("\nCounting rows in CSV...")
    total_rows = sum(1 for _ in open(csv_path)) - 1  # Subtract header
    print(f"Total rows to process: {total_rows:,}")
    
    # Define year columns
    year_columns = [str(year) for year in range(1972, 2025)]
    
    # Track unique values for reference tables
    countries_set = set()
    sectors_set = set()
    indicators_dict = {}  # key: indicator_code, value: (name, description)
    years_set = set()
    
    # First pass: collect unique reference data
    print("\n📊 Phase 1: Analyzing data structure...")
    chunk_iterator = pd.read_csv(csv_path, chunksize=chunk_size)
    
    for chunk in tqdm(chunk_iterator, total=(total_rows // chunk_size) + 1, desc="Scanning"):
        countries_set.update(chunk['COUNTRY'].dropna().unique())
        sectors_set.update(chunk['SECTOR'].dropna().unique())
        
        # Collect indicator information
        for _, row in chunk.iterrows():
            indicator_code = row.get('SERIES_CODE')
            indicator_name = row.get('INDICATOR', row.get('SERIES_NAME', ''))
            description = row.get('FULL_DESCRIPTION', '')
            
            if pd.notna(indicator_code):
                indicators_dict[indicator_code] = (indicator_name, description)
    
    # Insert reference data
    print("\n📝 Phase 2: Populating reference tables...")
    
    # Insert countries
    print(f"  Inserting {len(countries_set)} countries...")
    for country in sorted(countries_set):
        cursor.execute('INSERT OR IGNORE INTO countries (country_name) VALUES (?)', (country,))
    
    # Insert sectors
    print(f"  Inserting {len(sectors_set)} sectors...")
    for sector in sorted(sectors_set):
        cursor.execute('INSERT OR IGNORE INTO sectors (sector_name) VALUES (?)', (sector,))
    
    # Insert years
    print(f"  Inserting years 1972-2024...")
    for year in range(1972, 2025):
        cursor.execute('INSERT OR IGNORE INTO time_periods (year) VALUES (?)', (year,))
        years_set.add(year)
    
    # Insert indicators
    print(f"  Inserting {len(indicators_dict)} indicators...")
    for code, (name, description) in indicators_dict.items():
        cursor.execute('''
            INSERT OR IGNORE INTO indicators (indicator_code, indicator_name, source, description)
            VALUES (?, ?, 'GFS', ?)
        ''', (code, name, description))
    
    conn.commit()
    
    # Create lookup dictionaries
    country_lookup = {name: id for id, name in cursor.execute('SELECT country_id, country_name FROM countries').fetchall()}
    sector_lookup = {name: id for id, name in cursor.execute('SELECT sector_id, sector_name FROM sectors').fetchall()}
    indicator_lookup = {code: id for id, code in cursor.execute('SELECT indicator_id, indicator_code FROM indicators WHERE source="GFS"').fetchall()}
    
    # Second pass: insert observations
    print("\n💾 Phase 3: Importing observations...")
    chunk_iterator = pd.read_csv(csv_path, chunksize=chunk_size)
    
    observations_count = 0
    
    for chunk in tqdm(chunk_iterator, total=(total_rows // chunk_size) + 1, desc="Importing"):
        observations = []
        
        for _, row in chunk.iterrows():
            country_id = country_lookup.get(row['COUNTRY'])
            sector_id = sector_lookup.get(row['SECTOR'])
            indicator_id = indicator_lookup.get(row['SERIES_CODE'])
            transformation = row.get('TYPE_OF_TRANSFORMATION')
            scale = row.get('SCALE')
            frequency = row.get('FREQUENCY')
            
            # Extract values for each year
            for year in year_columns:
                value = row.get(year)
                
                # Only insert if we have a valid value
                if pd.notna(value) and country_id and indicator_id:
                    observations.append((
                        country_id,
                        int(year),
                        sector_id,
                        indicator_id,
                        float(value),
                        transformation,
                        scale,
                        frequency
                    ))
        
        # Batch insert
        if observations:
            cursor.executemany('''
                INSERT INTO gfs_observations 
                (country_id, year, sector_id, indicator_id, value, transformation, scale, frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', observations)
            observations_count += len(observations)
    
    conn.commit()
    
    # Print summary
    print("\n" + "=" * 80)
    print("✅ GFS Import Complete!")
    print("=" * 80)
    print(f"Countries:     {len(countries_set):,}")
    print(f"Sectors:       {len(sectors_set):,}")
    print(f"Indicators:    {len(indicators_dict):,}")
    print(f"Years:         {len(years_set):,}")
    print(f"Observations:  {observations_count:,}")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    # Update this path to your actual CSV file location
    csv_file = "Dataset Nov 9 2025 IMF GFS 10.0.0.csv"
    
    if Path(csv_file).exists():
        import_gfs_data(csv_file)
    else:
        print(f"Error: Could not find {csv_file}")
        print("Please update the csv_file path in this script.")
