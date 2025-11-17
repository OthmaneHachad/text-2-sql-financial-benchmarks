# Dataset Description Report: Economic Data Integration Database

## Overview

This database integrates two major financial datasets for text-to-sql benchmarking:

1. **IMF Government Finance Statistics (GFS)**: Government financial indicators across sectors, countries, and time periods (1972-2024)
2. **World Bank Global Economic Monitor (GEM)**: 35 economic indicators including GDP, CPI, exchange rates, and trade metrics

**Database Type**: SQLite (single-file relational database)  
**Primary Use**: Text-to-SQL benchmarking with real-world financial data  
**Domain**: Government finance and macroeconomic statistics

---

## Database Schema

The database follows a normalized relational structure with 6 core tables:

### Reference Tables

**1. countries**
- `country_id` (PK), `country_name`, `region`
- ~150-200 unique countries and economic regions

**2. time_periods**
- `year` (PK)
- Coverage: 1972-2024 (53 years)

**3. sectors**
- `sector_id` (PK), `sector_name`, `sector_description`
- ~20-30 government sectors (e.g., "Central government", "Social security funds")

**4. indicators**
- `indicator_id` (PK), `indicator_code`, `indicator_name`, `source`, `unit`, `description`
- 1000+ indicators total (split between GFS and GEM sources)

### Observation Tables

**5. gfs_observations**
- `observation_id` (PK), `country_id` (FK), `year` (FK), `sector_id` (FK), `indicator_id` (FK)
- `value`, `transformation`, `scale`, `frequency`
- Millions of observations
- Rich metadata including transformation types and scale factors

**6. gem_observations**
- `observation_id` (PK), `country_id` (FK), `year` (FK), `indicator_id` (FK)
- `value`, `seasonal_adjustment`
- Hundreds of thousands of observations
- Includes seasonal adjustment indicators

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
- **Total observations**: ~1-3 million records (combined GFS + GEM)
- **Unique countries**: 150-200
- **Indicators**: 1000+ unique indicators
- **Years covered**: 1972-2024
- **Database file size**: ~50-200 MB (varies by data completeness)

### Coverage Distribution
- **GFS data**: Government finance statistics with sector breakdowns
- **GEM data**: 35 economic indicator types across countries
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
