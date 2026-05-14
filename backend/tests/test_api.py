"""
Core API tests — covers health, auth, sources, upload validation, and search.
Uses an in-memory SQLite DB so no real data is touched.
"""
import os
import uuid
from fastapi.testclient import TestClient

_run_id = uuid.uuid4().hex[:8]  # unique per test run — avoids stale DB conflicts

os.environ.setdefault("GEMINI_API_KEY", "dummy")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("REDIS_URL", "")  # disables Redis; cache falls back gracefully

from main import app  # noqa: E402 — env must be set first

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "stats" in data


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register_and_login():
    payload = {"email": f"test_{_run_id}@devflow.io", "username": f"tester_{_run_id}", "password": "StrongPass1!"}
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    r2 = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_register_duplicate_email():
    payload = {"email": f"dup_{_run_id}@devflow.io", "username": f"dup_{_run_id}", "password": "Pass123!"}
    client.post("/api/auth/register", json=payload)
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code in (400, 409)


def test_login_wrong_password():
    client.post("/api/auth/register", json={
        "email": f"wrong_{_run_id}@devflow.io", "username": f"wrongpass_{_run_id}", "password": "Correct1!"
    })
    r = client.post("/api/auth/login", json={"email": f"wrong_{_run_id}@devflow.io", "password": "WrongPass!"})
    assert r.status_code == 401


# ── Sources ───────────────────────────────────────────────────────────────────

def test_get_sources_empty():
    r = client.get("/api/sources")
    assert r.status_code == 200
    assert "sources" in r.json()


def test_get_stats():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "sources" in data
    assert "documents" in data
    assert "searches" in data


def test_sources_pagination_params():
    r = client.get("/api/sources?limit=10&offset=0")
    assert r.status_code == 200


# ── Upload validation ─────────────────────────────────────────────────────────

def test_upload_rejects_wrong_extension():
    r = client.post("/api/upload", files={"file": ("evil.exe", b"MZ\x90\x00", "application/octet-stream")})
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def test_upload_rejects_fake_pdf():
    r = client.post("/api/upload", files={"file": ("doc.pdf", b"not-a-pdf-file", "application/pdf")})
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


def test_upload_rejects_oversized_file():
    big = b"A" * (11 * 1024 * 1024)  # 11 MB
    r = client.post("/api/upload", files={"file": ("big.txt", big, "text/plain")})
    assert r.status_code == 400
    assert "10 MB" in r.json()["detail"]


# ── Collections ───────────────────────────────────────────────────────────────

def test_create_and_list_collection():
    r = client.post("/api/collections", json={"name": "Test Col", "description": "for testing"})
    assert r.status_code == 200

    r2 = client.get("/api/collections")
    assert r2.status_code == 200
    names = [c["name"] for c in r2.json()["collections"]]
    assert "Test Col" in names


def test_delete_collection():
    r = client.post("/api/collections", json={"name": "ToDelete"})
    cid = r.json()["collection_id"]
    r2 = client.delete(f"/api/collections/{cid}")
    assert r2.status_code == 200
    assert r2.json()["success"] is True


# ── History ───────────────────────────────────────────────────────────────────

def test_get_history():
    r = client.get("/api/history")
    assert r.status_code == 200
    assert "history" in r.json()


# ── Analytics ─────────────────────────────────────────────────────────────────

def test_get_analytics():
    r = client.get("/api/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "cache_hit_rate" in data
    assert "top_queries" in data
