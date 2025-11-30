"""
Guideline Manager for Enhanced MAGIC

Loads and optionally filters MAGIC guidelines to reduce token overhead.
"""
from pathlib import Path
from typing import List, Optional
import re


class GuidelineManager:
    """Manages MAGIC guidelines for SQL generation"""

    def __init__(self, guideline_path: Path, use_full_guideline: bool = True):
        """
        Initialize guideline manager

        Args:
            guideline_path: Path to MAGIC guideline file
            use_full_guideline: If True, use full guideline; if False, extract relevant patterns
        """
        self.guideline_path = guideline_path
        self.use_full_guideline = use_full_guideline
        self.full_guideline = self._load_guideline()
        self.patterns = self._extract_patterns()

    def _load_guideline(self) -> str:
        """Load the full MAGIC guideline"""
        with open(self.guideline_path, 'r') as f:
            return f.read()

    def _extract_patterns(self) -> List[dict]:
        """
        Extract individual mistake patterns from guideline

        Returns:
            List of dicts with 'keywords', 'pattern_text'
        """
        patterns = []

        # Split by "# N. Reminder of mistake" sections
        sections = re.split(r'# (\d+)\. Reminder of mistake', self.full_guideline)

        # sections will be: [intro, num1, content1, num2, content2, ...]
        # We need to pair up numbers with their content
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                pattern_num = sections[i]
                pattern_content = sections[i + 1]

                # Extract keywords from the section
                keywords = self._extract_keywords(pattern_content)

                pattern = {
                    'id': int(pattern_num),
                    'keywords': keywords,
                    'text': f"# {pattern_num}. Reminder of mistake{pattern_content}".strip()
                }
                patterns.append(pattern)

        return patterns

    def _extract_keywords(self, section: str) -> List[str]:
        """Extract relevant keywords from a pattern section"""
        keywords = []

        # Extract table names
        if 'gfs_observations' in section.lower():
            keywords.extend(['gfs', 'government', 'revenue', 'expenditure', 'tax'])
        if 'gem_observations' in section.lower():
            keywords.extend(['gem', 'gdp', 'economic', 'indicator', 'unemployment', 'stock'])

        # Extract SQL keywords
        if 'DISTINCT' in section:
            keywords.append('distinct')
        if 'ORDER BY' in section:
            keywords.extend(['order', 'sort', 'top', 'rank'])
        if 'JOIN' in section:
            keywords.extend(['join', 'country', 'sector', 'indicator'])
        if 'LIKE' in section:
            keywords.extend(['like', 'match', 'pattern', 'start', 'contain'])

        return keywords

    def get_guideline(self, question: Optional[str] = None, max_patterns: int = 5) -> str:
        """
        Get guideline text for a question

        Args:
            question: The user's question (optional, for filtering)
            max_patterns: Maximum number of patterns to include if filtering

        Returns:
            Guideline text to include in prompt
        """
        if self.use_full_guideline or question is None:
            return self.full_guideline

        # Filter relevant patterns based on question keywords
        question_lower = question.lower()
        relevant_patterns = []

        for pattern in self.patterns:
            # Check if any pattern keywords appear in question
            relevance_score = sum(
                1 for keyword in pattern['keywords']
                if keyword in question_lower
            )

            if relevance_score > 0:
                relevant_patterns.append((relevance_score, pattern))

        # Sort by relevance and take top N
        relevant_patterns.sort(key=lambda x: x[0], reverse=True)
        selected_patterns = [p[1] for p in relevant_patterns[:max_patterns]]

        # If no relevant patterns, use first N patterns
        if not selected_patterns:
            selected_patterns = self.patterns[:max_patterns]

        # Combine selected patterns
        if selected_patterns:
            filtered_guideline = "Common SQL Mistakes to Avoid:\n\n"
            filtered_guideline += "\n\n".join(p['text'] for p in selected_patterns)
            return filtered_guideline

        return self.full_guideline

    def get_stats(self) -> dict:
        """Get statistics about the guideline"""
        return {
            'total_patterns': len(self.patterns),
            'total_chars': len(self.full_guideline),
            'avg_pattern_chars': len(self.full_guideline) // max(len(self.patterns), 1)
        }


if __name__ == "__main__":
    # Test guideline manager
    from pathlib import Path
    import sys

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from enhanced_magic.config import GUIDELINE_PATH

    # Test full guideline
    print("=== Full Guideline ===")
    manager = GuidelineManager(GUIDELINE_PATH, use_full_guideline=True)
    stats = manager.get_stats()
    print(f"Total patterns: {stats['total_patterns']}")
    print(f"Total chars: {stats['total_chars']}")
    print(f"Avg pattern chars: {stats['avg_pattern_chars']}")

    # Test filtered guideline
    print("\n=== Filtered Guideline ===")
    manager_filtered = GuidelineManager(GUIDELINE_PATH, use_full_guideline=False)

    test_question = "Show government revenue for Australia from 2010 to 2020"
    filtered = manager_filtered.get_guideline(test_question, max_patterns=3)
    print(f"Question: {test_question}")
    print(f"Filtered guideline length: {len(filtered)} chars")
    print(f"Reduction: {(1 - len(filtered)/len(manager.full_guideline))*100:.1f}%")
