from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app

MGR = ("manager@demo.vn", "Manager@123")


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as cl:
        yield cl


def tok(c, email, pw):
    r = c.post("/auth/login", data={"username": email, "password": pw})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def student(c, email):
    c.post("/auth/register", json={"email": email, "full_name": "Sinh Vien", "password": "secret1"})
    return tok(c, email, "secret1")


def new_event(c, cap=1, start=-1, end=1):
    h, n = tok(c, *MGR), datetime.now()
    r = c.post("/events", headers=h, json={
        "club_id": 1, "title": "Test event", "location": "P101", "capacity": cap, "points": 5,
        "start_time": (n + timedelta(hours=start)).isoformat(timespec="seconds"),
        "end_time": (n + timedelta(hours=end)).isoformat(timespec="seconds")})
    assert r.status_code == 201
    return r.json()["id"], h


def test_register_ok(c):
    r = c.post("/auth/register", json={"email": "a@x.vn", "full_name": "An", "password": "secret1"})
    assert r.status_code == 201


def test_register_duplicate_409(c):
    body = {"email": "dup@x.vn", "full_name": "Dup", "password": "secret1"}
    c.post("/auth/register", json=body)
    assert c.post("/auth/register", json=body).status_code == 409


def test_register_invalid_email_422(c):
    r = c.post("/auth/register", json={"email": "sai", "full_name": "An", "password": "secret1"})
    assert r.status_code == 422


def test_login_wrong_password_401(c):
    r = c.post("/auth/login", data={"username": MGR[0], "password": "sai"})
    assert r.status_code == 401


def test_no_token_401(c):
    assert c.get("/auth/me").status_code == 401


def test_student_cannot_create_club_403(c):
    h = student(c, "s1@x.vn")
    assert c.post("/clubs", headers=h, json={"name": "CLB Trái phép"}).status_code == 403


def test_manager_creates_club_and_duplicate_409(c):
    h = tok(c, *MGR)
    assert c.post("/clubs", headers=h, json={"name": "CLB Âm nhạc"}).status_code == 201
    assert c.post("/clubs", headers=h, json={"name": "CLB Âm nhạc"}).status_code == 409


def test_event_invalid_time_422(c):
    h, n = tok(c, *MGR), datetime.now()
    r = c.post("/events", headers=h, json={
        "club_id": 1, "title": "Sai giờ", "location": "A", "capacity": 5,
        "start_time": n.isoformat(), "end_time": (n - timedelta(hours=1)).isoformat()})
    assert r.status_code == 422


def test_list_events_pagination(c):
    r = c.get("/events", params={"size": 1, "page": 1})
    assert r.status_code == 200 and len(r.json()) == 1


def test_capacity_full_409(c):
    eid, _ = new_event(c, cap=1)
    assert c.post(f"/events/{eid}/register", headers=student(c, "s2@x.vn")).status_code == 201
    assert c.post(f"/events/{eid}/register", headers=student(c, "s3@x.vn")).status_code == 409


def test_checkin_flow_awards_points(c):
    eid, mh = new_event(c, cap=5)
    sh = student(c, "s4@x.vn")
    c.post(f"/events/{eid}/register", headers=sh)
    code = c.post(f"/events/{eid}/qr", headers=mh).json()["code"]
    assert c.post(f"/events/{eid}/checkin", headers=sh, json={"code": "sai"}).status_code == 400
    assert c.post(f"/events/{eid}/checkin", headers=sh, json={"code": code}).status_code == 200
    assert c.post(f"/events/{eid}/checkin", headers=sh, json={"code": code}).status_code == 409
    assert c.get("/me/history", headers=sh).json()["total_points"] == 5


def test_export_excel_requires_manager(c):
    eid, mh = new_event(c)
    assert c.get(f"/events/{eid}/attendances/export", headers=student(c, "s5@x.vn")).status_code == 403
    assert c.get(f"/events/{eid}/attendances/export", headers=mh).status_code == 200