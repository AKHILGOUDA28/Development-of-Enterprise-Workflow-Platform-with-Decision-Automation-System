"""
uuid_utils_compat.py
---------------------
Monkey-patches the uuid_utils module to use Python's built-in uuid library.
This bypasses the DLL requirement enforced by Windows App Control policies.

Import this BEFORE importing anything from langchain.
"""

import sys
import uuid as _stdlib_uuid
from types import ModuleType


def _make_uuid7():
    """Generate a UUID7-like ID using random bits (v4 fallback)."""
    return _stdlib_uuid.uuid4()


# Build a fake uuid_utils module
_fake = ModuleType("uuid_utils")
_fake.uuid4   = _stdlib_uuid.uuid4
_fake.uuid7   = _make_uuid7
_fake.UUID    = _stdlib_uuid.UUID

# Build a fake uuid_utils.compat submodule
_fake_compat = ModuleType("uuid_utils.compat")
_fake_compat.uuid7 = _make_uuid7

# Inject into sys.modules so any import of uuid_utils finds our stub
sys.modules.setdefault("uuid_utils",        _fake)
sys.modules.setdefault("uuid_utils.compat", _fake_compat)
