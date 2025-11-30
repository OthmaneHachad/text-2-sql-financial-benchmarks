# Dataset Description Report: Economic Data Integration Database

## Overview

This database integrates two major financial datasets for text-to-SQL benchmarking:

1. **IMF Government Finance Statistics (GFS)**: Government financial indicators (revenue, expenditure, debt) across sectors, countries, and time periods
2. **World Bank Global Economic Monitor (GEM)**: Macroeconomic indicators (GDP, CPI, unemployment, exchange rates, trade metrics)

**Database Type**: SQLite (single-file relational database)
**Database Size**: 75 MB
**Primary Use**: Text-to-SQL benchmarking with real-world financial data
**Domain**: Government finance and macroeconomic statistics
**Time Coverage**: 1972-2024 (53 years)

---

## Database Schema

The database follows a normalized relational structure with 6 core tables:

### Reference Tables

**1. countries**
- `country_id` (PK), `country_name`, `region`
- 271 countries and economic regions

**2. time_periods**
- `year` (PK)
- Coverage: 1972-2024 (53 years)

**3. sectors**
- `sector_id` (PK), `sector_name`, `sector_description`
- 8 government sectors (e.g., "General government", "Central government", "Social security funds")

**4. indicators**
- `indicator_id` (PK), `indicator_code`, `indicator_name`, `source`, `unit`, `description`
- 102,468 indicator records (see note below on denormalization)
- ~70 unique indicator types (35 GFS + 35 GEM)

### Observation Tables

**5. gfs_observations**
- `observation_id` (PK), `country_id` (FK), `year` (FK), `sector_id` (FK), `indicator_id` (FK)
- `value`, `transformation`, `scale`, `frequency`
- 625,695 observations
- Rich metadata including transformation types and scale factors

**6. gem_observations**
- `observation_id` (PK), `country_id` (FK), `year` (FK), `indicator_id` (FK)
- `value`, `seasonal_adjustment`
- 85,039 observations
- Includes seasonal adjustment indicators (boolean)

### Entity-Relationship Structure

```
countries ──┬─── gfs_observations ─── indicators (source='GFS')
            │         │
time_periods ───────┤
            │         │
sectors ─────────────┘
            │
            └─── gem_observations ─── indicators (source='GEM')
```

---

## Key Characteristics

### Data Complexity

**Multi-table relationships**: 6 tables with foreign key constraints  
**Hierarchical structures**: Countries, sectors, and temporal hierarchies  
**Metadata richness**: Transformation types, scales, seasonal adjustments  
**Temporal scope**: 50+ years of historical data

### Domain-Specific Challenges

1. **Financial terminology**: Government revenue, expenditure, debt, deficit indicators
2. **Transformation ambiguity**: Various data transformations (YoY growth, cumulative, etc.)
3. **Scale factors**: Values in millions, billions, or percentages
4. **Sector complexity**: Multi-level government sector classifications
5. **Cross-dataset integration**: Joining GFS and GEM data requires understanding source differences

### Query Complexity Dimensions

- **Simple selection**: Single-table queries with basic filtering
- **Aggregation**: GROUP BY operations across countries, years, or sectors
- **Temporal analysis**: Time-series queries, year-over-year calculations, window functions
- **Multi-table joins**: Combining observations with reference tables (2-4 table joins)
- **Cross-dataset queries**: Joining GFS and GEM observations (complex 5-6 table joins)
- **Hierarchical queries**: Sector-level aggregations and drill-downs

---

## Benchmark Relevance

### Advantages for Text-to-SQL Research

**Real-world data**: Actual financial statistics vs. synthetic benchmark data  
**Production-like complexity**: Reflects enterprise database characteristics  
**Domain specificity**: Tests model understanding of financial terminology  
**Schema reasoning**: Requires understanding of multi-table relationships and foreign keys  
**Ambiguity handling**: Scale, transformation, and seasonal adjustment interpretation

### Comparison to Standard Benchmarks

| Aspect | Spider/WikiSQL | This Database |
|--------|---------------|---------------|
| Domain | General/synthetic | Financial (specialized) |
| Schema complexity | 1-5 tables | 6 tables with FKs |
| Terminology | Simple | Domain-specific |
| Data source | Synthetic | Real-world (IMF/World Bank) |
| Temporal depth | Limited | 50+ years |
| Metadata richness | Minimal | Extensive |


## Dataset Statistics

### Size Metrics
- **Total rows**: 813,534 (across all tables)
- **Observation records**: 710,734 (625,695 GFS + 85,039 GEM)
- **Countries**: 271
- **Government sectors**: 8
- **Indicator records**: 102,468 (denormalized)
- **Unique indicator types**: ~70 (35 GFS + 35 GEM)
- **Years covered**: 1972-2024 (53 years)
- **Database file size**: 75 MB

### Coverage Distribution
- **GFS data**: Government finance statistics with sector breakdowns (625,695 observations)
- **GEM data**: 35 macroeconomic indicator types (85,039 observations)
- **Temporal coverage**: Varies by indicator (older indicators have sparser data)


## Data Quality Notes

### Strengths
- Official data from authoritative sources (IMF, World Bank)
- Consistent country identifiers across datasets
- Well-documented indicators with metadata
- Proper normalization with foreign key constraints

### Limitations
- **Sparse historical data**: Early years (1972-1990s) have fewer observations
- **Country coverage variation**: Not all indicators available for all countries
- **Missing values**: Some country-year-indicator combinations lack data
- **Naming inconsistencies**: Country names may vary slightly between GFS and GEM sources

### Data Preprocessing Applied
- Normalized country names for consistency
- Extracted and standardized temporal data
- Created unified indicator taxonomy
- Established foreign key relationships
- Added performance indexes for query optimization

### Note on Indicator Denormalization

The `indicators` table contains 102,468 records due to **denormalization of GFS data**:

- **GFS source format**: Each indicator in the original IMF GFS dataset embeds country codes in the indicator code (e.g., `HKG.S13.G1.G1_TCB_CAB.XDC.A` for Hong Kong revenue)
- **Database implementation**: Country-indicator combinations are stored as separate rows (194 countries × ~528 indicator types = 102,433 GFS records)
- **Actual indicator types**: Only ~70 unique indicator concepts exist (35 GFS types + 35 GEM types)

**Example**: The indicator "Revenue, Transactions (cash basis)" appears 3,104 times in the `indicators` table - once for each country-sector combination.

**Impact on queries**: This denormalization does not affect query correctness. Queries filter by `indicator_name` (which correctly handles duplicates) and join with `country_id` to retrieve the appropriate data.

**Impact on benchmarks**: The schema representation sent to models contains only table structure (888 characters), not the 102K rows, so this does not affect text-to-SQL model performance.

---

## Technical Specifications

**Database Engine**: SQLite 3.x  
**Character Encoding**: UTF-8  
**File Format**: Single .db file (portable)  
**Indexing**: Optimized indexes on country_id, year, and indicator_id  
**Constraints**: Foreign keys enabled, NOT NULL on critical fields

---


**Last Updated**: November 2025  
**Data Sources**: IMF GFS 10.0.0, World Bank GEM
