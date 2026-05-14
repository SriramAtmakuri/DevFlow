"""
Test environment patches applied before main.py loads:
  1. Stub strawberry/graphql_schema — pydantic/strawberry version mismatch on
     local system (not an issue in Docker where deps are pinned).
  2. Swap passlib's bcrypt context for sha256_crypt — bcrypt 4.x+ enforces
     the 72-byte password limit which breaks passlib's own wrap-bug detection.
     sha256_crypt has identical API and is fine for testing auth flow.
"""
import sys
from unittest.mock import MagicMock
from fastapi import APIRouter
from passlib.context import CryptContext

# 1. Stub graphql — must happen before `import main`
_gql_stub = MagicMock()
_gql_stub.graphql_router = APIRouter()
sys.modules.setdefault("strawberry", MagicMock())
sys.modules["graphql_schema"] = _gql_stub

# 2. Patch pwd_context — import auth module early and swap hasher
import auth.auth as _auth_module  # noqa: E402
_auth_module.pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
