"""Test configuration"""

import sys
from pathlib import Path

# Add backend directory to Python path for tests
# This allows tests to be run from both backend/ and backend/app/tests/
backend_dir = Path(__file__).resolve().parent.parent.parent
app_dir = backend_dir / "app"

for path in [str(backend_dir), str(app_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as backend for anyio"""
    return "asyncio"