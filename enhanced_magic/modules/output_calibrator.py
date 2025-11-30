"""
Output Calibrator - Reuses FinSQL's calibration component

This module provides a wrapper around FinSQL's output calibration.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import FinSQL's output calibrator
from finsql.modules.output_calibrator import OutputCalibrator

__all__ = ['OutputCalibrator']
