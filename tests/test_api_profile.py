from datetime import datetime

import pytest

from tests.conftest import buat_profil_dengan_token


def test_put_profile_baru_mengembalikan_201_dan_token_tanpa_token_hash(client):
    payload = {
        "nama": "Fikri",
        "skor": {"visual": 8, "aural": 5, "read_write": 7, "kinestetik": 4},
    }
    resp = client.put("/api/v1/profile/u01", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == "u01"
    assert data["nama"] == "Fikri"
    assert data["skor"] == payload["skor"]
    assert datetime.fromisoformat(data["dibuat_pada"])
    assert "token" in data and len(data["token"]) >= 32
    assert "token_hash" not in data


def test_get_profile_dengan_token_sendiri_mengembalikan_200(client):
    payload = {
        "nama": "Fikri",
        "skor": {"visual": 9, "aural": 6, "read_write": 8, "kinestetik": 3},
    }
    headers = buat_profil_dengan_token(client, user_id="u01", nama="Fikri", skor=payload["skor"])

    resp = client.get("/api/v1/profile/u01", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "u01"
    assert data["nama"] == "Fikri"
    assert data["skor"] == payload["skor"]
    assert "token" not in data
    assert "token_hash" not in data


def test_get_profile_tanpa_token_401_dan_token_pengguna_lain_403(client):
    buat_profil_dengan_token(client, user_id="u01")
    headers_u02 = buat_profil_dengan_token(client, user_id="u02", nama="Intan")

    # Tanpa token -> 401 + header WWW-Authenticate: Bearer
    resp_401 = client.get("/api/v1/profile/u01")
    assert resp_401.status_code == 401
    assert resp_401.headers.get("WWW-Authenticate") == "Bearer"

    # Token milik pengguna lain -> 403
    resp_403 = client.get("/api/v1/profile/u01", headers=headers_u02)
    assert resp_403.status_code == 403


def test_get_profile_user_tak_ada_dengan_token_sah_mengembalikan_403(client):
    # Token sah milik u01, tetapi mengakses profil user_tidak_ada (bukan miliknya) -> 403
    headers_u01 = buat_profil_dengan_token(client, user_id="u01")
    resp = client.get("/api/v1/profile/user_tidak_ada", headers=headers_u01)
    assert resp.status_code == 403


def test_put_profile_sudah_ada_otorisasi_dan_pembaruan_200_tanpa_token(client):
    payload_awal = {
        "nama": "Nama Lama",
        "skor": {"visual": 2, "aural": 2, "read_write": 2, "kinestetik": 2},
    }
    payload_baru = {
        "nama": "Nama Baru",
        "skor": {"visual": 10, "aural": 7, "read_write": 9, "kinestetik": 6},
    }

    resp_awal = client.put("/api/v1/profile/u01", json=payload_awal)
    assert resp_awal.status_code == 201
    dibuat_pada_awal = resp_awal.json()["dibuat_pada"]
    headers_u01 = {"Authorization": f"Bearer {resp_awal.json()['token']}"}
    headers_u02 = buat_profil_dengan_token(client, user_id="u02", nama="Intan")

    # Tanpa header -> 401
    resp_401 = client.put("/api/v1/profile/u01", json=payload_baru)
    assert resp_401.status_code == 401
    assert resp_401.headers.get("WWW-Authenticate") == "Bearer"

    # Token pengguna lain -> 403
    resp_403 = client.put("/api/v1/profile/u01", json=payload_baru, headers=headers_u02)
    assert resp_403.status_code == 403

    # Token sendiri -> 200 tanpa field token di respons
    resp_200 = client.put("/api/v1/profile/u01", json=payload_baru, headers=headers_u01)
    assert resp_200.status_code == 200
    data_200 = resp_200.json()
    assert "token" not in data_200
    assert "token_hash" not in data_200
    assert data_200["nama"] == "Nama Baru"
    assert data_200["skor"] == payload_baru["skor"]
    assert data_200["dibuat_pada"] == dibuat_pada_awal


@pytest.mark.parametrize(
    "header_salah",
    [
        {"Authorization": "Token abc"},
        {"Authorization": "Bearer "},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer token_tidak_terdaftar"},
    ],
)
def test_header_authorization_salah_bentuk_atau_tak_dikenal_mengembalikan_401(
    client, header_salah
):
    buat_profil_dengan_token(client, user_id="u01")

    resp_get = client.get("/api/v1/profile/u01", headers=header_salah)
    assert resp_get.status_code == 401
    assert resp_get.headers.get("WWW-Authenticate") == "Bearer"

    resp_put = client.put(
        "/api/v1/profile/u01",
        json={
            "nama": "Fikri",
            "skor": {"visual": 8, "aural": 5, "read_write": 7, "kinestetik": 4},
        },
        headers=header_salah,
    )
    assert resp_put.status_code == 401
    assert resp_put.headers.get("WWW-Authenticate") == "Bearer"


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