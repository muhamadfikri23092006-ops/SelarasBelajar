import pytest

from services.tools.effort import MENIT_DASAR

JENIS_VALID = next(iter(MENIT_DASAR.keys()))


def _buat_profil_contoh(client, user_id: str = "u01") -> None:
    resp = client.put(
        f"/api/v1/profile/{user_id}",
        json={
            "nama": "Fikri",
            "skor": {"visual": 8, "aural": 5, "read_write": 7, "kinestetik": 4},
        },
    )
    assert resp.status_code == 200


def test_post_task_valid_mengembalikan_201_dan_status_baru(client):
    _buat_profil_contoh(client, "u01")
    payload = {
        "user_id": "u01",
        "judul": "Rangkuman Sistem Operasi",
        "jenis": JENIS_VALID,
        "bobot": 0.5,
        "tenggat": "2026-11-25T23:59:00",
    }

    resp = client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data["id"], int)
    assert data["user_id"] == "u01"
    assert data["judul"] == "Rangkuman Sistem Operasi"
    assert data["jenis"] == JENIS_VALID
    assert data["bobot"] == 0.5
    assert data["status"] == "BARU"
    assert data["blok"] == []


def test_post_task_user_tak_terdaftar_mengembalikan_404(client):
    payload = {
        "user_id": "user_tidak_ada",
        "judul": "Rangkuman Bab 1",
        "jenis": JENIS_VALID,
        "bobot": 0.5,
        "tenggat": "2026-11-25T23:59:00",
    }

    resp = client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 404
    assert "detail" in resp.json()


@pytest.mark.parametrize(
    ("judul", "jenis", "bobot"),
    [
        ("Judul Valid", "jenis_ngawur", 0.5),
        ("Judul Valid", JENIS_VALID, 1.5),
        ("", JENIS_VALID, 0.5),
    ],
)
def test_post_task_input_invalid_mengembalikan_422(client, judul, jenis, bobot):
    _buat_profil_contoh(client, "u01")
    payload = {
        "user_id": "u01",
        "judul": judul,
        "jenis": jenis,
        "bobot": bobot,
        "tenggat": "2026-11-25T23:59:00",
    }

    resp = client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 422


def test_post_task_tenggat_format_salah_mengembalikan_422(client):
    _buat_profil_contoh(client, "u01")
    payload = {
        "user_id": "u01",
        "judul": "Rangkuman Bab 2",
        "jenis": JENIS_VALID,
        "bobot": 0.5,
        "tenggat": "besok jam 5",
    }

    resp = client.post("/api/v1/tasks", json=payload)
    assert resp.status_code == 422


def test_get_tasks_terurut_dari_tenggat_paling_dekat(client):
    _buat_profil_contoh(client, "u01")

    client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Tugas Jauh",
            "jenis": JENIS_VALID,
            "bobot": 0.8,
            "tenggat": "2026-12-10T23:59:00",
        },
    )
    client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Tugas Dekat",
            "jenis": JENIS_VALID,
            "bobot": 0.3,
            "tenggat": "2026-11-20T12:00:00",
        },
    )

    resp = client.get("/api/v1/tasks", params={"user_id": "u01"})
    assert resp.status_code == 200
    daftar = resp.json()
    assert len(daftar) == 2
    assert [item["judul"] for item in daftar] == ["Tugas Dekat", "Tugas Jauh"]


def test_get_tasks_user_tanpa_tugas_mengembalikan_200_dan_list_kosong(client):
    _buat_profil_contoh(client, "u01")
    resp = client.get("/api/v1/tasks", params={"user_id": "u01"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_tasks_tanpa_user_id_mengembalikan_422(client):
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 422