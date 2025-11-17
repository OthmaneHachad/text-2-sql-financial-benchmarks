"""
Master Setup Script
Orchestrates the complete database setup and data import process.
"""

import sys
from pathlib import Path
from datetime import datetime

def print_header(text):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def check_prerequisites():
    """Check if all required files and dependencies are available."""
    print_header("Step 0: Checking Prerequisites")
    
    issues = []
    
    # Check for required files
    gfs_file = "Dataset Nov 9 2025 IMF GFS 10.0.0.csv"
    gem_dir = "Gem Data Extraction"
    
    if not Path(gfs_file).exists():
        issues.append(f"❌ GFS CSV file not found: {gfs_file}")
    else:
        print(f"✓ Found GFS file: {gfs_file}")
    
    if not Path(gem_dir).exists():
        issues.append(f"❌ GEM directory not found: {gem_dir}")
    else:
        excel_files = list(Path(gem_dir).glob("*.xlsx"))
        print(f"✓ Found GEM directory with {len(excel_files)} Excel files")
    
    # Check for required Python packages
    try:
        import pandas
        print("✓ pandas is installed")
    except ImportError:
        issues.append("❌ pandas is not installed. Run: pip install pandas")
    
    try:
        import openpyxl
        print("✓ openpyxl is installed")
    except ImportError:
        issues.append("❌ openpyxl is not installed. Run: pip install openpyxl")
    
    try:
        import tqdm
        print("✓ tqdm is installed")
    except ImportError:
        issues.append("❌ tqdm is not installed. Run: pip install tqdm")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print("\n✅ All prerequisites satisfied!")
    return True

def run_setup():
    """Run the complete database setup process."""
    start_time = datetime.now()
    
    print_header("Economic Data Integration - Master Setup")
    print("This script will:")
    print("  1. Create the SQLite database with proper schema")
    print("  2. Import IMF Government Finance Statistics (GFS) data")
    print("  3. Import World Bank Global Economic Monitor (GEM) data")
    print("  4. Validate the imported data")
    print("  5. Run example queries")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Setup cannot proceed. Please resolve the issues above.")
        return False
    
    # Import required modules
    from database_setup import create_database
    from import_gfs_data import import_gfs_data
    from import_gem_data import import_gem_data
    from validate_data import validate_database
    from query_examples import example_queries
    
    # Step 1: Create database
    print_header("Step 1: Creating Database Schema")
    try:
        db_path = create_database()
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    # Step 2: Import GFS data
    print_header("Step 2: Importing GFS Data")
    try:
        import_gfs_data("Dataset Nov 9 2025 IMF GFS 10.0.0.csv", db_path)
    except Exception as e:
        print(f"❌ Error importing GFS data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Import GEM data
    print_header("Step 3: Importing GEM Data")
    try:
        import_gem_data("Gem Data Extraction", db_path)
    except Exception as e:
        print(f"❌ Error importing GEM data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Validate data
    print_header("Step 4: Validating Data")
    try:
        validation_passed = validate_database(db_path)
        if not validation_passed:
            print("⚠️  Some validation checks failed, but the database was created.")
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False
    
    # Step 5: Run example queries
    print_header("Step 5: Running Example Queries")
    try:
        example_queries(db_path)
    except Exception as e:
        print(f"⚠️  Error running example queries: {e}")
        # Don't fail the entire setup for this
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("Setup Complete!")
    print(f"✅ Database created successfully: {Path(db_path).absolute()}")
    print(f"⏱️  Total time: {duration:.1f} seconds")
    print(f"\nYou can now use this database for Text-to-SQL benchmarking!")
    print(f"\nNext steps:")
    print(f"  1. Explore the database using: python query_examples.py")
    print(f"  2. Connect to it programmatically: sqlite3.connect('{db_path}')")
    print(f"  3. Use it for your Text-to-SQL research and benchmarking")
    
    return True

if __name__ == "__main__":
    success = run_setup()
    sys.exit(0 if success else 1)
