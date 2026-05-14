"""
API integration tests — covers health, auth, sources, upload validation,
collections, history, analytics, and job status.
Uses an isolated SQLite DB (configured in conftest.py).
"""
import uuid
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
_run = uuid.uuid4().hex[:8]  # unique per test run


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register(suffix: str = "") -> dict:
    suffix = suffix or uuid.uuid4().hex[:6]
    r = client.post("/api/auth/register", json={
        "email": f"user_{suffix}@test.io",
        "username": f"user_{suffix}",
        "password": "TestPass1!",
    })
    assert r.status_code == 200, r.text
    return r.json()


def _auth_headers(suffix: str = "") -> dict:
    data = _register(suffix)
    return {"Authorization": f"Bearer {data['access_token']}"}


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "database" in body["checks"]
    assert "redis" in body["checks"]
    assert "version" in body


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "stats" in body


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register_returns_token():
    r = client.post("/api/auth/register", json={
        "email": f"tok_{_run}@test.io",
        "username": f"tok_{_run}",
        "password": "StrongPass1!",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["user_id"]
    assert body["username"] == f"tok_{_run}"


def test_login_returns_token():
    email = f"login_{_run}@test.io"
    client.post("/api/auth/register", json={"email": email, "username": f"login_{_run}", "password": "Pass123!"})
    r = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_register_duplicate_rejected():
    payload = {"email": f"dup_{_run}@test.io", "username": f"dup_{_run}", "password": "Pass123!"}
    client.post("/api/auth/register", json=payload)
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code in (400, 409)


def test_login_wrong_password():
    email = f"wrong_{_run}@test.io"
    client.post("/api/auth/register", json={"email": email, "username": f"wrong_{_run}", "password": "Correct1!"})
    r = client.post("/api/auth/login", json={"email": email, "password": "BadPass!"})
    assert r.status_code == 401


def test_logout():
    # Login with an already-registered user (avoids extra register call that could hit rate limit)
    email = f"login_{_run}@test.io"
    r = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    r2 = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["success"] is True


# ── Sources ───────────────────────────────────────────────────────────────────

def test_get_sources_empty():
    r = client.get("/api/sources")
    assert r.status_code == 200
    assert "sources" in r.json()


def test_get_sources_pagination():
    r = client.get("/api/sources?limit=10&offset=0")
    assert r.status_code == 200
    sources = r.json()["sources"]
    assert isinstance(sources, list)
    assert len(sources) <= 10


def test_get_stats_shape():
    r = client.get("/api/stats")
    assert r.status_code == 200
    body = r.json()
    for key in ("sources", "documents", "searches", "chromadb_count"):
        assert key in body, f"missing key: {key}"
        assert isinstance(body[key], int)


# ── Upload validation ─────────────────────────────────────────────────────────

def test_upload_rejects_wrong_extension():
    r = client.post("/api/upload", files={"file": ("evil.exe", b"MZ\x90\x00", "application/octet-stream")})
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def test_upload_rejects_fake_pdf():
    r = client.post("/api/upload", files={"file": ("doc.pdf", b"not-a-real-pdf", "application/pdf")})
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


def test_upload_rejects_oversized():
    big = b"A" * (11 * 1024 * 1024)
    r = client.post("/api/upload", files={"file": ("big.txt", big, "text/plain")})
    assert r.status_code == 400
    assert "10 MB" in r.json()["detail"]


def test_upload_txt_queues_job():
    content = b"This is a plain text document with enough content to be indexed properly."
    r = client.post("/api/upload", files={"file": ("sample.txt", content, "text/plain")})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "job_id" in body
    assert len(body["job_id"]) > 0


def test_job_status_not_found():
    r = client.get("/api/upload/status/nonexistent-job-id")
    assert r.status_code == 404


def test_job_status_after_queue():
    content = b"Another test document with sufficient text for indexing purposes."
    r = client.post("/api/upload", files={"file": ("test2.txt", content, "text/plain")})
    job_id = r.json()["job_id"]
    r2 = client.get(f"/api/upload/status/{job_id}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["job_id"] == job_id
    assert body["status"] in ("pending", "indexing", "completed", "failed")


# ── Collections ───────────────────────────────────────────────────────────────

def test_create_and_list_collection():
    r = client.post("/api/collections", json={"name": f"col_{_run}", "description": "test collection"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "collection_id" in body

    r2 = client.get("/api/collections")
    assert r2.status_code == 200
    names = [c["name"] for c in r2.json()["collections"]]
    assert f"col_{_run}" in names


def test_delete_collection():
    r = client.post("/api/collections", json={"name": f"del_{_run}"})
    assert r.status_code == 200
    cid = r.json()["collection_id"]

    r2 = client.delete(f"/api/collections/{cid}")
    assert r2.status_code == 200
    assert r2.json()["success"] is True

    r3 = client.get("/api/collections")
    ids = [c["id"] for c in r3.json()["collections"]]
    assert cid not in ids


def test_collection_no_description():
    r = client.post("/api/collections", json={"name": f"nodesc_{_run}"})
    assert r.status_code == 200


# ── History ───────────────────────────────────────────────────────────────────

def test_get_history_shape():
    r = client.get("/api/history")
    assert r.status_code == 200
    body = r.json()
    assert "history" in body
    assert isinstance(body["history"], list)


def test_get_history_limit():
    r = client.get("/api/history?limit=5")
    assert r.status_code == 200
    assert len(r.json()["history"]) <= 5


def test_history_limit_bounds():
    r = client.get("/api/history?limit=0")
    assert r.status_code == 422  # pydantic validation: ge=1


# ── Analytics ─────────────────────────────────────────────────────────────────

def test_get_analytics_shape():
    r = client.get("/api/analytics")
    assert r.status_code == 200
    body = r.json()
    for key in ("cache_hit_rate", "top_queries", "searches_by_day", "source_types", "model_usage"):
        assert key in body, f"missing analytics key: {key}"


def test_analytics_cache_hit_rate_type():
    r = client.get("/api/analytics")
    rate = r.json()["cache_hit_rate"]
    assert isinstance(rate, (int, float))
    assert 0.0 <= rate <= 100.0


# ── Manual document index ─────────────────────────────────────────────────────

def test_manual_index_queues():
    r = client.post("/api/index/manual", json={
        "title": "Test Doc",
        "content": "This is a sufficiently long test document for testing the manual indexing endpoint.",
        "url": "https://example.com/test",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "source_id" in body
