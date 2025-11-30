"""
Smart MAGIC + Dataset-Specific Guidelines

Extends Smart MAGIC with targeted guideline patterns that address
observed failure modes from error analysis.

This follows MAGIC's core methodology: observe failures → create guidelines
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.smart_inference import SmartMAGIC


class SmartMAGICWithGuidelines(SmartMAGIC):
    """
    Smart MAGIC + Dataset-Specific Guidelines

    Extends Smart MAGIC with additional guideline patterns targeting:
    1. GFS vs GEM dataset confusion
    2. Wrong indicator names
    3. Missing columns in SELECT
    """

    def __init__(self, verbose: bool = False):
        """Initialize Smart MAGIC with enhanced guidelines"""
        super().__init__(verbose=verbose)

        # Add dataset-specific guidelines to existing MAGIC guideline
        self.enhanced_guideline = self._build_enhanced_guideline()

        if self.verbose:
            print(f"✓ Enhanced with dataset-specific guidelines")
            print(f"  Original guideline: {len(self.guideline)} chars")
            print(f"  Enhanced guideline: {len(self.enhanced_guideline)} chars\n")

    def _build_enhanced_guideline(self) -> str:
        """Build enhanced guideline with dataset-specific patterns"""

        dataset_guidelines = """

=== DATASET-SPECIFIC GUIDELINES (Based on Error Analysis) ===

# 10. Choose the correct observation dataset (GFS vs GEM)

CRITICAL: We have two separate observation tables with different data types:

**GFS Dataset (gfs_observations):**
- Government Finance Statistics - fiscal and public finance data
- Use for: government revenue, government expenditure, tax revenue, social benefits, government debt, fiscal policy, public spending
- Always requires JOIN with sectors table (General government, Central government, Local government)
- Keywords that indicate GFS: "government", "revenue", "expenditure", "tax", "social benefits", "fiscal", "public", "sector", "debt"

**GEM Dataset (gem_observations):**
- Global Economic Monitor - macroeconomic indicators
- Use for: GDP, stock market, unemployment rate, inflation, terms of trade, exchange rates, economic growth
- Does NOT have sectors (no sector_id column)
- Keywords that indicate GEM: "GDP", "stock market", "unemployment", "inflation", "terms of trade", "economic", "growth", "market"

**Common mistakes to avoid:**
- ❌ Using gfs_observations for "stock market index" or "GDP" → MUST use gem_observations
- ❌ Using gem_observations for "government revenue" or "tax" → MUST use gfs_observations
- ❌ Joining gem_observations with sectors table → GEM has no sector_id column
- ❌ Looking for economic indicators in GFS → Check GEM first for macro indicators

**Decision rule:**
1. Does the question mention "government", "fiscal", "tax", "public", or "sector"? → Use gfs_observations
2. Does the question mention "GDP", "stock market", "unemployment", "inflation", or general "economic" indicators? → Use gem_observations
3. Still unsure? Check which dataset has the indicator in the indicators table

# 11. Use exact indicator names from the database

Do NOT guess, abbreviate, or use LIKE patterns for indicator names. Always use exact matches.

**Common GFS indicators (exact names):**
- Revenue: "Revenue, Transactions (cash basis of recording), Cash basis"
- Expenditure: "Expenditure, Transactions (cash basis of recording), Cash basis"
- Social benefits: "Social benefits, Transactions (cash basis of recording), Cash basis"

**For any indicator:**
- ✓ CORRECT: WHERE i.indicator_name = 'Unemployment Rate'
- ❌ WRONG: WHERE i.indicator_name LIKE '%unemployment%'
- ❌ WRONG: WHERE i.indicator_name = 'Unemployment' (missing exact suffix)

**Best practice:**
If uncertain about exact indicator name, use a subquery to check:
```sql
SELECT indicator_name FROM indicators WHERE indicator_name LIKE '%keyword%'
```
Then use the exact name in your main query.

# 12. Include ALL requested columns in SELECT clause

When question asks "Show X for Y from year1 to year2" or similar time-series questions:

**Required columns:**
- ✓ MUST include: year column (for time-series context)
- ✓ MUST include: the metric/value being asked about
- ✓ SHOULD include: country/entity name if comparing across entities
- ✓ MUST add: ORDER BY year for time-series results

**Common mistakes:**
- ❌ Returning only value without year: `SELECT value FROM ...`
- ❌ Returning only year without value: `SELECT year FROM ...`
- ❌ Forgetting ORDER BY for time-series: Missing `ORDER BY year`

**Examples:**
- Question: "Show GDP for USA from 2010 to 2020"
  ✓ Correct: `SELECT year, value AS gdp FROM gem_observations ... ORDER BY year`
  ❌ Wrong: `SELECT value FROM gem_observations ...` (missing year)

- Question: "List top 5 countries by observations"
  ✓ Correct: `SELECT country_name, COUNT(*) AS obs_count ... ORDER BY obs_count DESC LIMIT 5`
  ❌ Wrong: `SELECT country_name ... LIMIT 5` (missing count in SELECT)

# 13. For aggregation questions, use GROUP BY not DISTINCT

**When to use GROUP BY:**
- Questions with "per", "by", "each", "for every", "average by", "count by"
- Need aggregation functions: COUNT(), AVG(), SUM(), MAX(), MIN()

**Common mistakes:**
- ❌ Using DISTINCT when you need aggregation: `SELECT DISTINCT country_name, year FROM ...`
- ✓ Correct approach: `SELECT year, COUNT(DISTINCT country_id) FROM ... GROUP BY year`

**Examples:**
- Question: "Count countries per year" or "Count countries for each year"
  ✓ Correct: `SELECT year, COUNT(DISTINCT country_id) AS count FROM ... GROUP BY year`
  ❌ Wrong: `SELECT DISTINCT country_name, year FROM ...`

- Question: "Average value by sector"
  ✓ Correct: `SELECT sector_name, AVG(value) FROM ... GROUP BY sector_name`
  ❌ Wrong: `SELECT DISTINCT sector_name, value FROM ...`

=== END DATASET-SPECIFIC GUIDELINES ===
"""

        # Combine original MAGIC guideline with dataset-specific patterns
        enhanced = self.guideline + dataset_guidelines
        return enhanced

    def _build_prompt(self, question: str, smart_schema: str) -> str:
        """Build prompt with smart schema and ENHANCED guidelines"""

        prompt = f"""You are an expert SQL query generator for an economic database.

Database Schema:
{smart_schema}

Question: {question}

IMPORTANT GUIDELINES - Common Mistakes to Avoid:

{self.enhanced_guideline}

Instructions:
1. Generate a valid SQL query that accurately answers the question
2. Use tables from PRIMARY TABLES first (most relevant)
3. You can also use OTHER AVAILABLE TABLES if needed for JOINs
4. Follow the guidelines above to avoid common mistakes
5. Pay special attention to:
   - Choosing the correct dataset (GFS vs GEM)
   - Using exact indicator names
   - Including all requested columns in SELECT
   - Using GROUP BY for aggregation questions
6. For time-series questions, include year column in SELECT and ORDER BY year
7. Return ONLY the SQL query, no explanations

SQL Query:"""

        return prompt


if __name__ == "__main__":
    # Quick test
    smart_guidelines = SmartMAGICWithGuidelines(verbose=True)

    # Test with a query that previously failed due to dataset confusion
    test_questions = [
        "Show the stock market index for the United Kingdom from 2015 to 2023",  # Should use GEM
        "Show government revenue (percent of GDP) for Australia from 2010 to 2020",  # Should use GFS
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")

        result = smart_guidelines.generate(question, top_k_detailed=3)

        print(f"\nGenerated SQL:")
        print(result['sql'])
        print(f"\nRanked tables: {result['ranked_tables'][:3]}")
