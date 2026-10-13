from .conftest import JOB, RESUME, signup


def upload_resume(client, auth, text=RESUME):
    return client.post("/api/resumes", headers=auth,
                       files={"file": ("resume.txt", text.encode(), "text/plain")})


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_signup_login_me(client):
    auth = signup(client)
    assert client.get("/api/auth/me", headers=auth).json()["email"] == "a@example.com"
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrongpass1"}).status_code == 401


def test_duplicate_signup_and_short_password(client):
    signup(client)
    r = client.post("/api/auth/signup", json={"email": "A@example.com", "password": "password123"})
    assert r.status_code == 409
    r = client.post("/api/auth/signup", json={"email": "b@example.com", "password": "short"})
    assert r.status_code == 422


def test_requires_auth(client):
    assert client.get("/api/jobs").status_code == 401
    assert client.get("/api/jobs", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_resume_upload_extracts_skills(client, auth):
    r = upload_resume(client, auth)
    assert r.status_code == 201, r.text
    skills = r.json()["skills"]
    assert "python" in skills and "docker" in skills
    assert client.get("/api/resumes/latest", headers=auth).json()["filename"] == "resume.txt"


def test_resume_rejects_bad_files(client, auth):
    r = client.post("/api/resumes", headers=auth, files={"file": ("x.exe", b"abc", "application/octet-stream")})
    assert r.status_code == 400
    assert upload_resume(client, auth, text="too short").status_code == 400


def test_job_extraction_and_match(client, auth):
    upload_resume(client, auth)
    r = client.post("/api/jobs", headers=auth, json={"raw_text": JOB, "url": "https://example.com/job"})
    assert r.status_code == 201, r.text
    job = r.json()
    assert job["company"] == "Acme Robotics"
    assert job["title"] == "AI Engineer"
    assert "kubernetes" in job["required_skills"]
    assert "langchain" in job["nice_to_have_skills"]
    assert 0 <= job["match_score"] <= 100
    assert "python" in job["matched_skills"]
    assert "kubernetes" in job["missing_skills"]
    assert job["match_summary"]


def test_job_without_resume_has_no_score(client, auth):
    job = client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).json()
    assert job["match_score"] is None
    assert client.post(f"/api/jobs/{job['id']}/tailor", headers=auth).status_code == 400


def test_new_resume_rescores_existing_jobs(client, auth):
    job = client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).json()
    upload_resume(client, auth)
    assert client.get(f"/api/jobs/{job['id']}", headers=auth).json()["match_score"] is not None


def test_status_flow_and_dashboard(client, auth):
    upload_resume(client, auth)
    ids = [client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).json()["id"] for _ in range(3)]
    r = client.patch(f"/api/jobs/{ids[0]}", headers=auth, json={"status": "applied"})
    assert r.json()["applied_at"] is not None
    client.patch(f"/api/jobs/{ids[1]}", headers=auth, json={"status": "interview"})
    assert client.patch(f"/api/jobs/{ids[2]}", headers=auth, json={"status": "hired!"}).status_code == 422

    d = client.get("/api/dashboard", headers=auth).json()
    assert d["total"] == 3
    assert d["by_status"]["saved"] == 1
    assert d["interview_rate"] == 50.0
    assert d["applied_this_week"] == 1
    assert d["top_missing_skills"][0]["count"] == 3


def test_tailor(client, auth):
    upload_resume(client, auth)
    job = client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).json()
    r = client.post(f"/api/jobs/{job['id']}/tailor", headers=auth)
    assert r.status_code == 200
    assert len(r.json()["tailored_bullets"]) >= 1
    assert "Acme Robotics" in r.json()["cover_letter"]


def test_users_cannot_see_each_others_jobs(client, auth):
    job = client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).json()
    other = signup(client, "b@example.com")
    assert client.get(f"/api/jobs/{job['id']}", headers=other).status_code == 404
    assert client.delete(f"/api/jobs/{job['id']}", headers=other).status_code == 404
    assert client.get("/api/jobs", headers=other).json() == []


def test_delete_job(client, auth):
    job = client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).json()
    assert client.delete(f"/api/jobs/{job['id']}", headers=auth).status_code == 204
    assert client.get(f"/api/jobs/{job['id']}", headers=auth).status_code == 404


def test_rate_limit(client, auth, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "AI_CALLS_PER_HOUR", 2)
    for _ in range(2):
        assert client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).status_code == 201
    assert client.post("/api/jobs", headers=auth, json={"raw_text": JOB}).status_code == 429
