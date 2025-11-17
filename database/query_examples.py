"""
Query Examples Script
Demonstrates common query patterns for Text-to-SQL benchmarking.
"""

import sqlite3
import pandas as pd
from pathlib import Path

def run_query(cursor, query_name, query, description):
    """Execute a query and display results."""
    print(f"\n{'=' * 80}")
    print(f"📊 {query_name}")
    print(f"{'=' * 80}")
    print(f"Description: {description}")
    print(f"\nSQL Query:")
    print("-" * 80)
    print(query)
    print("-" * 80)
    
    try:
        df = pd.read_sql_query(query, cursor.connection)
        print(f"\nResults ({len(df)} rows):")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error executing query: {e}")

def example_queries(db_path='economic_data.db'):
    """
    Run example queries that demonstrate Text-to-SQL capabilities.
    """
    print("=" * 80)
    print("Text-to-SQL Example Queries")
    print("=" * 80)
    
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query 1: Simple aggregation
    query1 = """
    SELECT 
        c.country_name,
        COUNT(DISTINCT g.indicator_id) as num_indicators,
        COUNT(*) as num_observations
    FROM gfs_observations g
    JOIN countries c ON g.country_id = c.country_id
    GROUP BY c.country_name
    ORDER BY num_observations DESC
    LIMIT 10
    """
    run_query(cursor, "Query 1: Top 10 Countries by GFS Data Coverage", query1,
              "Which countries have the most comprehensive GFS data?")
    
    # Query 2: Time-series comparison
    query2 = """
    SELECT 
        g.year,
        c.country_name,
        i.indicator_name,
        g.value
    FROM gfs_observations g
    JOIN countries c ON g.country_id = c.country_id
    JOIN indicators i ON g.indicator_id = i.indicator_id
    WHERE c.country_name = 'United States'
        AND g.year BETWEEN 2015 AND 2023
        AND i.indicator_name LIKE '%Revenue%'
    ORDER BY g.year, i.indicator_name
    LIMIT 20
    """
    run_query(cursor, "Query 2: US Revenue Indicators Over Time", query2,
              "Show revenue-related indicators for the United States from 2015-2023")
    
    # Query 3: Cross-country comparison
    query3 = """
    SELECT 
        c.country_name,
        AVG(g.value) as avg_value
    FROM gem_observations g
    JOIN countries c ON g.country_id = c.country_id
    JOIN indicators i ON g.indicator_id = i.indicator_id
    WHERE i.indicator_name LIKE '%GDP%'
        AND g.year = 2020
        AND c.country_name IN ('United States', 'China', 'Germany', 'Japan', 'United Kingdom')
    GROUP BY c.country_name
    ORDER BY avg_value DESC
    """
    run_query(cursor, "Query 3: GDP Comparison Across Major Economies (2020)", query3,
              "Compare average GDP values for major economies in 2020")
    
    # Query 4: Join across GFS and GEM
    query4 = """
    SELECT 
        c.country_name,
        gfs.year,
        gfs_i.indicator_name as gfs_indicator,
        gfs.value as gfs_value,
        gem_i.indicator_name as gem_indicator,
        gem.value as gem_value
    FROM gfs_observations gfs
    JOIN countries c ON gfs.country_id = c.country_id
    JOIN indicators gfs_i ON gfs.indicator_id = gfs_i.indicator_id
    JOIN gem_observations gem ON gfs.country_id = gem.country_id AND gfs.year = gem.year
    JOIN indicators gem_i ON gem.indicator_id = gem_i.indicator_id
    WHERE c.country_name = 'Germany'
        AND gfs.year = 2020
        AND gfs_i.indicator_name LIKE '%Revenue%'
        AND gem_i.indicator_name LIKE '%GDP%'
    LIMIT 10
    """
    run_query(cursor, "Query 4: Combining GFS and GEM Data", query4,
              "Show both government revenue (GFS) and GDP (GEM) data for Germany in 2020")
    
    # Query 5: Complex aggregation with sectors
    query5 = """
    SELECT 
        s.sector_name,
        COUNT(DISTINCT g.indicator_id) as unique_indicators,
        COUNT(DISTINCT g.country_id) as countries_covered,
        COUNT(*) as total_observations
    FROM gfs_observations g
    JOIN sectors s ON g.sector_id = s.sector_id
    WHERE g.year >= 2010
    GROUP BY s.sector_name
    ORDER BY total_observations DESC
    LIMIT 10
    """
    run_query(cursor, "Query 5: Sector Coverage Analysis", query5,
              "Analyze data coverage by government sector since 2010")
    
    # Query 6: Year-over-year growth calculation
    query6 = """
    WITH yearly_data AS (
        SELECT 
            c.country_name,
            g.year,
            AVG(g.value) as avg_value
        FROM gem_observations g
        JOIN countries c ON g.country_id = c.country_id
        JOIN indicators i ON g.indicator_id = i.indicator_id
        WHERE i.indicator_name LIKE '%CPI%'
            AND c.country_name IN ('United States', 'United Kingdom', 'Japan')
            AND g.year BETWEEN 2018 AND 2023
        GROUP BY c.country_name, g.year
    )
    SELECT 
        country_name,
        year,
        avg_value,
        LAG(avg_value) OVER (PARTITION BY country_name ORDER BY year) as prev_year_value,
        ROUND(
            ((avg_value - LAG(avg_value) OVER (PARTITION BY country_name ORDER BY year)) 
             / LAG(avg_value) OVER (PARTITION BY country_name ORDER BY year)) * 100, 
            2
        ) as yoy_growth_pct
    FROM yearly_data
    ORDER BY country_name, year
    """
    run_query(cursor, "Query 6: Year-over-Year CPI Growth", query6,
              "Calculate year-over-year growth rates for CPI across countries")
    
    # Query 7: Data availability analysis
    query7 = """
    SELECT 
        g.year,
        COUNT(DISTINCT g.country_id) as countries_with_data,
        COUNT(DISTINCT g.indicator_id) as indicators_available,
        COUNT(*) as total_observations
    FROM gfs_observations g
    WHERE g.year >= 2000
    GROUP BY g.year
    ORDER BY g.year DESC
    """
    run_query(cursor, "Query 7: GFS Data Availability by Year", query7,
              "Track the availability of GFS data over time since 2000")
    
    # Query 8: Indicator popularity
    query8 = """
    SELECT 
        i.indicator_name,
        i.source,
        COUNT(DISTINCT CASE WHEN i.source = 'GFS' THEN g.country_id END) as gfs_countries,
        COUNT(DISTINCT CASE WHEN i.source = 'GEM' THEN gem.country_id END) as gem_countries,
        COUNT(CASE WHEN i.source = 'GFS' THEN g.observation_id END) as gfs_observations,
        COUNT(CASE WHEN i.source = 'GEM' THEN gem.observation_id END) as gem_observations
    FROM indicators i
    LEFT JOIN gfs_observations g ON i.indicator_id = g.indicator_id
    LEFT JOIN gem_observations gem ON i.indicator_id = gem.indicator_id
    GROUP BY i.indicator_name, i.source
    ORDER BY 
        CASE WHEN i.source = 'GFS' THEN gfs_observations ELSE gem_observations END DESC
    LIMIT 15
    """
    run_query(cursor, "Query 8: Most Common Indicators", query8,
              "Identify the most frequently reported indicators in each dataset")
    
    print(f"\n{'=' * 80}")
    print("✅ Query examples complete!")
    print(f"{'=' * 80}\n")
    
    # Generate Text-to-SQL benchmark template
    print("\n📝 Text-to-SQL Benchmark Template")
    print("=" * 80)
    print("""
These example queries can be adapted for Text-to-SQL benchmarking:

1. Simple Selection: "What countries have GFS data available?"
2. Aggregation: "What is the average GDP for each country in 2020?"
3. Filtering: "Show me revenue data for Germany between 2015 and 2020"
4. Joining: "Compare GDP and government revenue for the US"
5. Time-series: "Calculate year-over-year growth in CPI"
6. Complex: "Which sector has the most complete data coverage since 2010?"
7. Multi-table: "Show countries that appear in both GFS and GEM datasets"
8. Grouping: "How many indicators are available for each sector?"

For your Text-to-SQL research, you can:
- Generate natural language questions
- Use these queries as gold-standard SQL
- Test different prompt engineering techniques
- Evaluate Text-to-SQL model performance
    """)
    
    conn.close()

if __name__ == "__main__":
    example_queries()
