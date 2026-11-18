from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app, get_koneksi
from services.storage.db import init_db


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test_profile.db"

    def override_get_koneksi():
        koneksi = init_db(db_path)
        try:
            yield koneksi
        finally:
            koneksi.close()

    app.dependency_overrides[get_koneksi] = override_get_koneksi
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_put_profile_valid_mengembalikan_200(client):
    payload = {
        "nama": "Fikri",
        "skor": {"visual": 8, "aural": 5, "read_write": 7, "kinestetik": 4},
    }
    resp = client.put("/api/v1/profile/u01", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "u01"
    assert data["nama"] == "Fikri"
    assert data["skor"] == payload["skor"]
    assert datetime.fromisoformat(data["dibuat_pada"])


def test_get_profile_setelah_put_mengembalikan_200_dan_skor_sama(client):
    payload = {
        "nama": "Fikri",
        "skor": {"visual": 9, "aural": 6, "read_write": 8, "kinestetik": 3},
    }
    client.put("/api/v1/profile/u01", json=payload)

    resp = client.get("/api/v1/profile/u01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "u01"
    assert data["nama"] == "Fikri"
    assert data["skor"] == payload["skor"]


def test_get_profile_user_tak_ada_mengembalikan_404(client):
    resp = client.get("/api/v1/profile/user_tidak_ada")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_put_profile_skor_negatif_mengembalikan_422(client):
    payload = {
        "nama": "Fikri",
        "skor": {"visual": -1, "aural": 5, "read_write": 7, "kinestetik": 4},
    }
    resp = client.put("/api/v1/profile/u01", json=payload)
    assert resp.status_code == 422


def test_put_profile_kunci_skor_kurang_mengembalikan_422(client):
    payload = {
        "nama": "Fikri",
        "skor": {"visual": 8, "aural": 5, "read_write": 7},
    }
    resp = client.put("/api/v1/profile/u01", json=payload)
    assert resp.status_code == 422


def test_put_profile_dua_kali_get_mengembalikan_data_terbaru(client):
    payload_awal = {
        "nama": "Nama Lama",
        "skor": {"visual": 2, "aural": 2, "read_write": 2, "kinestetik": 2},
    }
    payload_baru = {
        "nama": "Nama Baru",
        "skor": {"visual": 10, "aural": 7, "read_write": 9, "kinestetik": 6},
    }

    resp_awal = client.put("/api/v1/profile/u01", json=payload_awal)
    dibuat_pada_awal = resp_awal.json()["dibuat_pada"]

    client.put("/api/v1/profile/u01", json=payload_baru)
    resp_get = client.get("/api/v1/profile/u01")

    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["nama"] == "Nama Baru"
    assert data["skor"] == payload_baru["skor"]
    assert data["dibuat_pada"] == dibuat_pada_awal