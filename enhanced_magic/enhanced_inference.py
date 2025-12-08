"""
Enhanced MAGIC Inference Engine

Combines:
- MAGIC's proven guidelines
- FinSQL's schema linking
- FinSQL's self-consistency voting
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from together import Together
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_magic.config import (
    MODEL_NAME,
    API_KEY,
    GUIDELINE_PATH,
    DB_PATH,
    INFERENCE_CONFIG,
    SCHEMA_LINKING_CONFIG,
    CALIBRATION_CONFIG,
    GUIDELINE_CONFIG,
)
from enhanced_magic.modules.schema_linker import EmbeddingSchemaLinker
from enhanced_magic.modules.guideline_manager import GuidelineManager
from enhanced_magic.modules.output_calibrator import OutputCalibrator
from shared.database import format_schema


class EnhancedMAGIC:
    """
    Enhanced MAGIC: Multi-Agent Guideline with Schema Linking and Self-Consistency

    Architecture:
    1. Schema Linking (FinSQL) - Retrieves relevant tables/columns
    2. Guideline-Enhanced Prompting (MAGIC) - Generates N candidates
    3. Self-Consistency Voting (FinSQL) - Selects best candidate
    """

    def __init__(
        self,
        num_samples: Optional[int] = None,
        use_full_guideline: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize Enhanced MAGIC

        Args:
            num_samples: Number of candidates to generate (default from config)
            use_full_guideline: Use full guideline or filter relevant patterns
            verbose: Print debug information
        """
        self.num_samples = num_samples or INFERENCE_CONFIG["num_samples"]
        self.verbose = verbose

        # Initialize components
        print("Initializing Enhanced MAGIC...")

        # 1. Schema Linker (FinSQL)
        if self.verbose:
            print("  Loading schema linker...")
        self.schema_linker = EmbeddingSchemaLinker(
            db_path=str(DB_PATH),
            model_name=SCHEMA_LINKING_CONFIG["model_name"],
        )

        # 2. Guideline Manager (MAGIC)
        if self.verbose:
            print("  Loading MAGIC guideline...")
        self.guideline_manager = GuidelineManager(
            guideline_path=GUIDELINE_PATH,
            use_full_guideline=use_full_guideline,
        )

        # 3. Output Calibrator (FinSQL)
        if self.verbose:
            print("  Loading output calibrator...")
        self.calibrator = OutputCalibrator(db_path=str(DB_PATH))

        # 4. TogetherAI client
        if self.verbose:
            print("  Connecting to TogetherAI...")

        if not API_KEY:
            raise ValueError(
                "TOGETHER_API_KEY not found. Please set it as an environment variable.\n"
                "You can set it with: export TOGETHER_API_KEY='your-api-key'"
            )

        # Initialize client with 180 second timeout
        self.client = Together(api_key=API_KEY, timeout=180.0)
        self.model_name = MODEL_NAME

        # Get full schema for reference
        self.full_schema = format_schema(str(DB_PATH))

        print("✓ Enhanced MAGIC initialized")

    def _build_prompt(self, question: str, linked_schema: str, guideline: str) -> str:
        """Build prompt with schema, question, and guidelines"""

        prompt = f"""You are an expert SQL query generator for an economic database.

Database Schema (relevant tables and columns):
{linked_schema}

Question: {question}

{guideline}

Instructions:
1. Generate a valid SQL query that accurately answers the question
2. Use only tables and columns from the provided schema
3. Follow SQL best practices (use DISTINCT when needed, ORDER BY for rankings, etc.)
4. Avoid the common mistakes listed in the guidelines
5. Return ONLY the SQL query, no explanations

SQL Query:"""

        return prompt

    def generate(
        self,
        question: str,
        return_candidates: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate SQL query for a question

        Args:
            question: Natural language question
            return_candidates: If True, return all candidates with voting details

        Returns:
            Dict with 'sql', 'candidates', 'voting_details', 'linked_schema'
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Question: {question}")
            print(f"{'='*60}")

        # Step 1: Schema Linking
        if self.verbose:
            print("\n[1/3] Schema Linking...")

        linked_result = self.schema_linker.link_schema(
            question=question,
            top_k_tables=SCHEMA_LINKING_CONFIG["top_k_tables"],
            top_k_columns_per_table=SCHEMA_LINKING_CONFIG["top_k_columns"],
        )

        linked_schema = self.schema_linker.format_linked_schema(linked_result)

        if self.verbose:
            print(f"  Linked tables: {linked_result['linked_tables']}")
            print(f"  Schema length: {len(linked_schema)} chars")

        # Step 2: Get guideline
        guideline = self.guideline_manager.get_guideline(
            question=question,
            max_patterns=GUIDELINE_CONFIG.get("max_patterns", 5),
        )

        if self.verbose:
            print(f"\n[2/3] Guideline:")
            print(f"  Guideline length: {len(guideline)} chars")
            if not GUIDELINE_CONFIG["use_full_guideline"]:
                print(f"  (Filtered from {len(self.guideline_manager.full_guideline)} chars)")

        # Step 3: Generate candidates
        if self.verbose:
            print(f"\n[3/3] Generating {self.num_samples} candidates...")

        prompt = self._build_prompt(question, linked_schema, guideline)
        candidates = []
        raw_outputs = []

        for i in range(self.num_samples):
            if self.verbose:
                print(f"  Candidate {i+1}/{self.num_samples}...", end=" ")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=INFERENCE_CONFIG["max_tokens"],
                temperature=INFERENCE_CONFIG["temperature"],
                top_p=INFERENCE_CONFIG["top_p"],
            )

            raw_output = response.choices[0].message.content.strip()
            raw_outputs.append(raw_output)

            # Extract SQL from response
            sql = self._extract_sql(raw_output)
            candidates.append(sql)

            if self.verbose:
                print(f"✓ ({len(sql)} chars)")

        # Step 4: Self-Consistency Voting
        if self.verbose:
            print("\n[4/4] Self-Consistency Voting...")

        # Use FinSQL's calibrate method (implements self-consistency)
        final_sql = self.calibrator.calibrate(candidates, return_all_valid=False)

        # Count votes for the selected SQL
        vote_count = sum(1 for c in candidates if c.strip().lower() == final_sql.strip().lower())

        if self.verbose:
            print(f"  Unique candidates: {len(set(candidates))}")
            print(f"  Selected SQL votes: {vote_count}/{len(candidates)}")
            print(f"\n{'='*60}")
            print(f"Final SQL:\n{final_sql}")
            print(f"{'='*60}\n")

        # Build result
        result = {
            "sql": final_sql,
            "linked_schema": linked_schema,
            "linked_tables": linked_result['linked_tables'],
            "num_candidates": len(candidates),
            "num_unique_candidates": len(set(candidates)),
            "vote_count": vote_count,
        }

        if return_candidates:
            result["candidates"] = candidates
            result["raw_outputs"] = raw_outputs

        return result

    def _extract_sql(self, text: str) -> str:
        """Extract SQL query from model output"""
        import re

        # Remove markdown code blocks
        text = re.sub(r'```sql\s*', '', text)
        text = re.sub(r'```\s*', '', text)

        # Look for SELECT statement
        match = re.search(r'(SELECT\s+.*?)(;|\Z)', text, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1).strip()
            return sql

        # If no SELECT found, return cleaned text
        return text.strip()


if __name__ == "__main__":
    # Test Enhanced MAGIC
    enhanced = EnhancedMAGIC(num_samples=3, verbose=True)

    # Test query
    test_question = "List all available sectors in the GFS data"

    result = enhanced.generate(test_question, return_candidates=True)

    print("\n=== RESULT ===")
    print(f"Question: {test_question}")
    print(f"Final SQL: {result['sql']}")
    print(f"Candidates: {result['num_candidates']}")
    print(f"Unique: {result['num_unique_candidates']}")
    print(f"Votes: {result['vote_count']}")
