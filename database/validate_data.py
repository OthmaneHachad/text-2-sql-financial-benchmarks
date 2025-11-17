"""
Database Validation Script
Validates the integrity and completeness of the imported data.
"""

import sqlite3
from pathlib import Path

def validate_database(db_path='economic_data.db'):
    """
    Run comprehensive validation checks on the database.
    
    Args:
        db_path: Path to the SQLite database
    """
    print("=" * 80)
    print("Database Validation")
    print("=" * 80)
    
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    all_checks_passed = True
    
    # Check 1: Table existence
    print("\n1️⃣  Checking table structure...")
    expected_tables = ['countries', 'time_periods', 'sectors', 'indicators', 
                      'gfs_observations', 'gem_observations']
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    for table in expected_tables:
        if table in existing_tables:
            print(f"  ✓ Table '{table}' exists")
        else:
            print(f"  ❌ Table '{table}' missing!")
            all_checks_passed = False
    
    # Check 2: Record counts
    print("\n2️⃣  Checking record counts...")
    
    tables_to_check = {
        'countries': 'Countries',
        'time_periods': 'Time periods',
        'sectors': 'Sectors',
        'indicators': 'Indicators',
        'gfs_observations': 'GFS observations',
        'gem_observations': 'GEM observations'
    }
    
    for table, label in tables_to_check.items():
        if table in existing_tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"  ✓ {label}: {count:,} records")
            else:
                print(f"  ⚠️  {label}: 0 records (table is empty)")
                all_checks_passed = False
    
    # Check 3: Foreign key integrity
    print("\n3️⃣  Checking foreign key relationships...")
    
    # Check GFS observations
    cursor.execute('''
        SELECT COUNT(*) FROM gfs_observations 
        WHERE country_id NOT IN (SELECT country_id FROM countries)
    ''')
    orphan_gfs = cursor.fetchone()[0]
    
    if orphan_gfs == 0:
        print(f"  ✓ GFS observations: All country references valid")
    else:
        print(f"  ❌ GFS observations: {orphan_gfs} invalid country references")
        all_checks_passed = False
    
    # Check GEM observations
    cursor.execute('''
        SELECT COUNT(*) FROM gem_observations 
        WHERE country_id NOT IN (SELECT country_id FROM countries)
    ''')
    orphan_gem = cursor.fetchone()[0]
    
    if orphan_gem == 0:
        print(f"  ✓ GEM observations: All country references valid")
    else:
        print(f"  ❌ GEM observations: {orphan_gem} invalid country references")
        all_checks_passed = False
    
    # Check 4: Data completeness
    print("\n4️⃣  Checking data completeness...")
    
    # Check for null values in critical fields
    cursor.execute('''
        SELECT COUNT(*) FROM gfs_observations WHERE value IS NULL
    ''')
    null_gfs = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM gem_observations WHERE value IS NULL
    ''')
    null_gem = cursor.fetchone()[0]
    
    print(f"  ℹ️  GFS null values: {null_gfs:,}")
    print(f"  ℹ️  GEM null values: {null_gem:,}")
    
    # Check 5: Year range coverage
    print("\n5️⃣  Checking year coverage...")
    
    cursor.execute('''
        SELECT MIN(year), MAX(year) FROM gfs_observations
    ''')
    gfs_years = cursor.fetchone()
    if gfs_years[0]:
        print(f"  ✓ GFS data: {gfs_years[0]} to {gfs_years[1]}")
    
    cursor.execute('''
        SELECT MIN(year), MAX(year) FROM gem_observations
    ''')
    gem_years = cursor.fetchone()
    if gem_years[0]:
        print(f"  ✓ GEM data: {gem_years[0]} to {gem_years[1]}")
    
    # Check 6: Duplicate detection
    print("\n6️⃣  Checking for duplicates...")
    
    cursor.execute('''
        SELECT country_id, year, sector_id, indicator_id, COUNT(*) as cnt
        FROM gfs_observations
        GROUP BY country_id, year, sector_id, indicator_id
        HAVING cnt > 1
    ''')
    gfs_dupes = cursor.fetchall()
    
    if len(gfs_dupes) == 0:
        print(f"  ✓ GFS: No duplicates found")
    else:
        print(f"  ⚠️  GFS: {len(gfs_dupes)} duplicate groups found")
    
    cursor.execute('''
        SELECT country_id, year, indicator_id, COUNT(*) as cnt
        FROM gem_observations
        GROUP BY country_id, year, indicator_id
        HAVING cnt > 1
    ''')
    gem_dupes = cursor.fetchall()
    
    if len(gem_dupes) == 0:
        print(f"  ✓ GEM: No duplicates found")
    else:
        print(f"  ⚠️  GEM: {len(gem_dupes)} duplicate groups found")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("📊 Database Summary Statistics")
    print("=" * 80)
    
    cursor.execute('SELECT COUNT(DISTINCT country_name) FROM countries')
    print(f"Unique Countries:     {cursor.fetchone()[0]:,}")
    
    cursor.execute('SELECT COUNT(*) FROM sectors')
    print(f"Sectors:              {cursor.fetchone()[0]:,}")
    
    cursor.execute('SELECT COUNT(*) FROM indicators WHERE source="GFS"')
    gfs_indicators = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM indicators WHERE source="GEM"')
    gem_indicators = cursor.fetchone()[0]
    print(f"GFS Indicators:       {gfs_indicators:,}")
    print(f"GEM Indicators:       {gem_indicators:,}")
    
    cursor.execute('SELECT COUNT(*) FROM gfs_observations')
    print(f"GFS Observations:     {cursor.fetchone()[0]:,}")
    
    cursor.execute('SELECT COUNT(*) FROM gem_observations')
    print(f"GEM Observations:     {cursor.fetchone()[0]:,}")
    
    # Database size
    db_size = Path(db_path).stat().st_size / (1024 * 1024)  # MB
    print(f"\nDatabase File Size:   {db_size:.2f} MB")
    
    print("=" * 80)
    
    if all_checks_passed:
        print("\n✅ All validation checks passed!")
    else:
        print("\n⚠️  Some validation checks failed. Please review the issues above.")
    
    conn.close()
    return all_checks_passed

if __name__ == "__main__":
    validate_database()
