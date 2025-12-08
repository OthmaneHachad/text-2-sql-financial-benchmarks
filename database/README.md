# Database Setup

This directory contains scripts to create and populate the economic database used for Text-to-SQL experiments.

## Overview

The database integrates two major economic datasets:
1. **IMF Government Finance Statistics (GFS)**: Government finance data with 105 columns (1972-2024)
2. **World Bank Global Economic Monitor (GEM)**: Economic indicators from 35 Excel files

**Result**: Normalized relational SQLite database with 6 tables and millions of observations.

---

## Quick Start

### One-Command Setup

```bash
python master_setup.py
```

This creates `economic_data.db` automatically.


---

## Database Schema

```
economic_data.db (SQLite)
├── countries          (country_id, country_name, region)
├── time_periods       (year)
├── sectors            (sector_id, sector_name, sector_description)
├── indicators         (indicator_id, indicator_code, indicator_name, source, unit)
├── gfs_observations   (observation_id, country_id, year, sector_id, indicator_id, value, ...)
└── gem_observations   (observation_id, country_id, year, indicator_id, value, ...)
```

### Table Details

**countries**
- `country_id` (INTEGER PRIMARY KEY)
- `country_name` (TEXT)
- `region` (TEXT)

**time_periods**
- `year` (INTEGER PRIMARY KEY)

**sectors** (GFS only)
- `sector_id` (INTEGER PRIMARY KEY)
- `sector_name` (TEXT)
- `sector_description` (TEXT)

**indicators**
- `indicator_id` (INTEGER PRIMARY KEY)
- `indicator_code` (TEXT)
- `indicator_name` (TEXT)
- `source` (TEXT): 'GFS' or 'GEM'
- `unit` (TEXT)

**gfs_observations**
- `observation_id` (INTEGER PRIMARY KEY)
- `country_id` (INTEGER FOREIGN KEY → countries)
- `year` (INTEGER FOREIGN KEY → time_periods)
- `sector_id` (INTEGER FOREIGN KEY → sectors)
- `indicator_id` (INTEGER FOREIGN KEY → indicators)
- `value` (REAL)
- Additional metadata columns

**gem_observations**
- `observation_id` (INTEGER PRIMARY KEY)
- `country_id` (INTEGER FOREIGN KEY → countries)
- `year` (INTEGER FOREIGN KEY → time_periods)
- `indicator_id` (INTEGER FOREIGN KEY → indicators)
- `value` (REAL)

---

## Scripts

### 1. master_setup.py

**Orchestrates full database setup**

```bash
python master_setup.py
```

**What it does**:
1. Checks prerequisites (raw data files exist)
2. Creates database schema
3. Imports GFS data
4. Imports GEM data
5. Validates data integrity
6. Runs example queries

**Prerequisites**:
- `Dataset Nov 9 2025 IMF GFS 10.0.0.csv` (in project root)
- `Gem Data Extraction/` folder with 35 Excel files (in project root)

### 2. database_setup.py

**Creates database schema only**

```bash
python database_setup.py
```

Creates empty `economic_data.db` with all 6 tables.

### 3. import_gfs_data.py

**Imports IMF GFS data**

```bash
python import_gfs_data.py
```

**What it does**:
- Reads `Dataset Nov 9 2025 IMF GFS 10.0.0.csv`
- Populates `countries`, `time_periods`, `sectors`, `indicators`, `gfs_observations`
- Handles data cleaning and normalization


### 4. import_gem_data.py

**Imports World Bank GEM data**

```bash
python import_gem_data.py
```

**What it does**:
- Reads 35 Excel files from `Gem Data Extraction/`
- Populates `gem_observations` and adds to `indicators`
- Handles wide-to-long transformation


### 5. validate_data.py

**Validates data integrity**

```bash
python validate_data.py
```

**Checks**:
- Row counts for each table
- Foreign key integrity
- Null value percentages
- Data range validity

### 6. query_examples.py

**Runs example queries**

```bash
python query_examples.py
```

**Example queries**:
- Simple selections
- JOIN operations
- Aggregations
- Complex multi-table queries

---

## File Structure

```
database/
├── README.md              # This file
├── master_setup.py        # One-command setup
├── database_setup.py      # Create schema
├── import_gfs_data.py     # Import GFS data
├── import_gem_data.py     # Import GEM data
├── validate_data.py       # Validate data
├── query_examples.py      # Example queries
└── economic_data.db       # Generated database (not tracked)
```

## Regenerating the Database

If `economic_data.db` is deleted or corrupted:

```bash
# Delete existing database
rm economic_data.db

# Regenerate from scratch
python master_setup.py
```

**Important**: You need the raw data files:
- `Dataset Nov 9 2025 IMF GFS 10.0.0.csv`
- `Gem Data Extraction/` folder

These are not tracked in git due to size constraints.

---

## Usage Examples

### Connect to Database

```python
import sqlite3
import pandas as pd

# Connect
conn = sqlite3.connect('economic_data.db')

# Run query
query = """
SELECT c.country_name, g.year, i.indicator_name, g.value
FROM gfs_observations g
JOIN countries c ON g.country_id = c.country_id
JOIN indicators i ON g.indicator_id = i.indicator_id
WHERE c.country_name = 'United States' AND g.year >= 2020
LIMIT 10
"""

df = pd.read_sql_query(query, conn)
print(df)

conn.close()
```

### Get Schema Information

```python
from shared.database import format_schema

# Get formatted schema for all tables
schema = format_schema('economic_data.db')
print(schema)
```

---

## Notes

- **Database file not tracked**: `economic_data.db` is excluded from git (.gitignore)
- **Regenerate as needed**: Scripts are idempotent (can run multiple times)
- **SQLite version**: Requires SQLite 3.7+
- **Encoding**: UTF-8 for all text fields

---

**Last Updated**: December 2025
