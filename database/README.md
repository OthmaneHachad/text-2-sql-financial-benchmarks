# Database

This directory contains database setup scripts and the SQLite database.

## Files
- `database_setup.py` - Creates database schema
- `import_gfs_data.py` - Imports GFS data
- `import_gem_data.py` - Imports GEM data
- `master_setup.py` - Orchestrates full setup
- `validate_data.py` - Validates imported data
- `query_examples.py` - Example queries for testing
- `economic_data.db` - The SQLite database (created by scripts)

## Usage
```bash
python master_setup.py
```
