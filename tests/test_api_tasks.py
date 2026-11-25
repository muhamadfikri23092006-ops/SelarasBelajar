import pytest

from services.tools.effort import MENIT_DASAR
from tests.conftest import buat_profil_dengan_token

JENIS_VALID = next(iter(MENIT_DASAR.keys()))


def _buat_profil_contoh(client, user_id: str = "u01") -> None:
    buat_profil_dengan_token(client, user_id=user_id)
    
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

# --- Tugas 11C: matkul, status_rencana, GET /tasks/{id}, PATCH /tasks/{id} ---


def test_post_task_dengan_dan_tanpa_matkul(client):
    _buat_profil_contoh(client, "u01")

    resp_tanpa = client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Tugas Tanpa Matkul",
            "jenis": JENIS_VALID,
            "bobot": 0.4,
            "tenggat": "2026-11-26T20:00:00",
        },
    )
    assert resp_tanpa.status_code == 201
    assert resp_tanpa.json()["matkul"] == ""

    resp_dengan = client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Tugas Dengan Matkul",
            "matkul": "Keamanan Informasi",
            "jenis": JENIS_VALID,
            "bobot": 0.6,
            "tenggat": "2026-11-26T20:00:00",
        },
    )
    assert resp_dengan.status_code == 201
    assert resp_dengan.json()["matkul"] == "Keamanan Informasi"


def test_post_task_baru_memuat_status_rencana_belum_direncanakan(client):
    _buat_profil_contoh(client, "u01")
    resp = client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Cek Status Rencana",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status_rencana"] == "BELUM_DIRENCANAKAN"


def test_get_task_by_id_200_dan_404(client):
    _buat_profil_contoh(client, "u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Detail Tugas",
            "matkul": "Manajemen Proyek",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
    )
    tugas_id = buat.json()["id"]

    resp_ok = client.get(f"/api/v1/tasks/{tugas_id}")
    assert resp_ok.status_code == 200
    assert resp_ok.json()["id"] == tugas_id
    assert resp_ok.json()["matkul"] == "Manajemen Proyek"

    resp_not_found = client.get("/api/v1/tasks/999999")
    assert resp_not_found.status_code == 404


def test_patch_task_status_sah_mengubah_nilai_dan_konsisten_di_get(client):
    _buat_profil_contoh(client, "u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Selesaikan Modul",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
    )
    tugas_id = buat.json()["id"]

    resp_patch = client.patch(
        f"/api/v1/tasks/{tugas_id}",
        json={"status": "SELESAI"},
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status"] == "SELESAI"
    assert resp_patch.json()["status_rencana"] == "BELUM_DIRENCANAKAN"

    resp_get = client.get(f"/api/v1/tasks/{tugas_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["status"] == "SELESAI"


def test_patch_task_status_tidak_sah_422_dan_id_tak_ada_404(client):
    _buat_profil_contoh(client, "u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "user_id": "u01",
            "judul": "Tes Validasi Patch",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
    )
    tugas_id = buat.json()["id"]

    resp_422 = client.patch(
        f"/api/v1/tasks/{tugas_id}",
        json={"status": "TERJADWAL"},
    )
    assert resp_422.status_code == 422

    resp_404 = client.patch(
        "/api/v1/tasks/999999",
        json={"status": "DIKERJAKAN"},
    )
    assert resp_404.status_code == 404