# Economic Data Integration for Text-to-SQL Research

This repository contains scripts to merge IMF Government Finance Statistics (GFS) and World Bank Global Economic Monitor (GEM) datasets into a unified SQLite database for Text-to-SQL benchmarking.

## 📊 Overview

This project integrates two major economic datasets:

1. **IMF GFS Dataset**: Government Finance Statistics with 105 columns including country, sector, indicator metadata, and yearly values (1972-2024)
2. **World Bank GEM Dataset**: 35 Excel files containing various economic indicators (GDP, CPI, Exchange Rates, etc.) across countries

The result is a normalized relational database perfect for complex SQL queries and Text-to-SQL model evaluation.

## 🗄️ Database Schema

```
economic_data.db
├── countries          (country_id, country_name, region)
├── time_periods       (year)
├── sectors            (sector_id, sector_name, sector_description)
├── indicators         (indicator_id, indicator_code, indicator_name, source, unit)
├── gfs_observations   (observation_id, country_id, year, sector_id, indicator_id, value, ...)
└── gem_observations   (observation_id, country_id, year, indicator_id, value, ...)
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** with the following packages:
```bash
pip install -r requirements.txt
```

2. **Data files**:
   - `Dataset Nov 9 2025 IMF GFS 10.0.0.csv` (in this directory)
   - `Gem Data Extraction/` folder with 35 Excel files

### One-Command Setup

Run the master setup script to create and populate the database automatically:

```bash
python master_setup.py
```

This will:
1. ✓ Check prerequisites
2. ✓ Create database schema
3. ✓ Import GFS data (~millions of observations)
4. ✓ Import GEM data from 35 Excel files
5. ✓ Validate data integrity
6. ✓ Run example queries

```

## 🔧 Manual Step-by-Step Setup

If you prefer to run steps individually:

### Step 1: Create Database
```bash
python database_setup.py
```

### Step 2: Import GFS Data
```bash
python import_gfs_data.py
```

### Step 3: Import GEM Data
```bash
python import_gem_data.py
```

### Step 4: Validate Data
```bash
python validate_data.py
```

### Step 5: Explore with Example Queries
```bash
python query_examples.py
```

## 💡 Usage Examples

### Connecting to the Database

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('your_db_file.db')

# Run a query
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


## 📈 Text-to-SQL Research Applications

This database is ideal for:

1. **Benchmarking Text-to-SQL Models**
   - Complex schema with foreign keys
   - Multiple related tables
   - Real-world financial data

2. **Testing Query Complexity**
   - Simple selections → Complex joins
   - Aggregations → Window functions
   - Single-table → Multi-table queries

3. **Domain-Specific Challenges**
   - Financial terminology
   - Temporal analysis
   - Cross-country comparisons
   - Sector-specific queries

4. **Schema Understanding**
   - Hierarchical relationships
   - Metadata interpretation
   - Scale and transformation handling

## 🔍 Data Statistics

After import, you should see approximately:
- **Countries**: ~150-200 unique countries
- **Indicators**: 
  - GFS: ~1000+ indicators
  - GEM: 35 indicators (one per Excel file)
- **Observations**:
  - GFS: ~millions of observations
  - GEM: ~hundreds of thousands of observations
- **Years**: 1972-2024 (varies by indicator)
- **Sectors**: ~20-30 government sectors (GFS only)

## 📝 Notes for Project



### Extending the Database

To add more data sources:
1. Follow the pattern in `import_gem_data.py` for new file types
2. Add new tables or extend existing schemas
3. Update `validate_data.py` to check new data
4. Document new query patterns in `query_examples.py`

## 📚 Additional Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [IMF GFS Methodology](https://www.imf.org/external/pubs/ft/gfs/manual/index.htm)
- [World Bank GEM](https://datacatalog.worldbank.org/dataset/global-economic-monitor)

## 📄 License

This code is for academic research purposes as part of Georgia Tech VIP program.
Data sources retain their respective licenses:
- IMF GFS: IMF Copyright and Usage
- World Bank GEM: Creative Commons Attribution 4.0

---

**Created for**: Georgia Tech VIP - Text-to-SQL Research  
**Last Updated**: November 2025
