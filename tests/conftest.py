"""
tests/conftest.py
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Provide test key by default for unit tests so live-key guard passes during testing
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_mock_for_unit_tests")
