"""
Test environment setup:
  1. Isolated SQLite DB per test run (via DATABASE_URL env var).
  2. Stub graphql_schema — avoids strawberry/pydantic version conflicts on local.
  3. Swap bcrypt → sha256_crypt in passlib to avoid bcrypt 4.x 72-byte limit issue.
"""
import os
import sys
import uuid
import tempfile
from unittest.mock import MagicMock
from fastapi import APIRouter
from passlib.context import CryptContext

# ── 1. Isolated test database ─────────────────────────────────────────────────

_tmp_db = os.path.join(tempfile.gettempdir(), f"devflow_test_{uuid.uuid4().hex[:8]}.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ.setdefault("GEMINI_API_KEY", "dummy")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("REDIS_URL", "")  # disables Redis; cache falls back gracefully
os.environ.setdefault("SENTRY_DSN", "")  # disable Sentry in tests

# ── 2. Stub graphql ───────────────────────────────────────────────────────────

_gql_stub = MagicMock()
_gql_stub.graphql_router = APIRouter()
sys.modules.setdefault("strawberry", MagicMock())
sys.modules["graphql_schema"] = _gql_stub

# ── 3. Patch pwd_context ──────────────────────────────────────────────────────

import auth.auth as _auth_module  # noqa: E402
_auth_module.pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

