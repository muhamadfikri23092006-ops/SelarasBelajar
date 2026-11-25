import pytest

from services.tools.effort import MENIT_DASAR
from tests.conftest import buat_profil_dengan_token

JENIS_VALID = next(iter(MENIT_DASAR.keys()))


def test_post_task_valid_mengembalikan_201_dan_status_baru(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    payload = {
        "judul": "Rangkuman Sistem Operasi",
        "jenis": JENIS_VALID,
        "bobot": 0.5,
        "tenggat": "2026-11-25T23:59:00",
    }

    resp = client.post("/api/v1/tasks", json=payload, headers=headers_a)
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data["id"], int)
    assert data["user_id"] == "u01"
    assert data["judul"] == "Rangkuman Sistem Operasi"
    assert data["jenis"] == JENIS_VALID
    assert data["bobot"] == 0.5
    assert data["status"] == "BARU"
    assert data["blok"] == []


def test_post_task_dengan_user_id_di_body_ditolak_422(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    payload = {
        "user_id": "u01",
        "judul": "Rangkuman Bab 1",
        "jenis": JENIS_VALID,
        "bobot": 0.5,
        "tenggat": "2026-11-25T23:59:00",
    }

    resp = client.post("/api/v1/tasks", json=payload, headers=headers_a)
    assert resp.status_code == 422


@pytest.mark.parametrize(
    ("judul", "jenis", "bobot"),
    [
        ("Judul Valid", "jenis_ngawur", 0.5),
        ("Judul Valid", JENIS_VALID, 1.5),
        ("", JENIS_VALID, 0.5),
    ],
)
def test_post_task_input_invalid_mengembalikan_422(client, judul, jenis, bobot):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    payload = {
        "judul": judul,
        "jenis": jenis,
        "bobot": bobot,
        "tenggat": "2026-11-25T23:59:00",
    }

    resp = client.post("/api/v1/tasks", json=payload, headers=headers_a)
    assert resp.status_code == 422


def test_post_task_tenggat_format_salah_mengembalikan_422(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    payload = {
        "judul": "Rangkuman Bab 2",
        "jenis": JENIS_VALID,
        "bobot": 0.5,
        "tenggat": "besok jam 5",
    }

    resp = client.post("/api/v1/tasks", json=payload, headers=headers_a)
    assert resp.status_code == 422


def test_get_tasks_terurut_dari_tenggat_paling_dekat(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")

    client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Jauh",
            "jenis": JENIS_VALID,
            "bobot": 0.8,
            "tenggat": "2026-12-10T23:59:00",
        },
        headers=headers_a,
    )
    client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Dekat",
            "jenis": JENIS_VALID,
            "bobot": 0.3,
            "tenggat": "2026-11-20T12:00:00",
        },
        headers=headers_a,
    )

    resp = client.get("/api/v1/tasks", headers=headers_a)
    assert resp.status_code == 200
    daftar = resp.json()
    assert len(daftar) == 2
    assert [item["judul"] for item in daftar] == ["Tugas Dekat", "Tugas Jauh"]


def test_get_tasks_user_tanpa_tugas_mengembalikan_200_dan_list_kosong(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    resp = client.get("/api/v1/tasks", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json() == []


# --- Tugas 11C & Tugas 13: matkul, status_rencana, GET/PATCH & Proteksi Auth ---


def test_post_task_dengan_dan_tanpa_matkul(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")

    resp_tanpa = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Tanpa Matkul",
            "jenis": JENIS_VALID,
            "bobot": 0.4,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    assert resp_tanpa.status_code == 201
    assert resp_tanpa.json()["matkul"] == ""

    resp_dengan = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Dengan Matkul",
            "matkul": "Keamanan Informasi",
            "jenis": JENIS_VALID,
            "bobot": 0.6,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    assert resp_dengan.status_code == 201
    assert resp_dengan.json()["matkul"] == "Keamanan Informasi"


def test_post_task_baru_memuat_status_rencana_belum_direncanakan(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    resp = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Cek Status Rencana",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    assert resp.status_code == 201
    assert resp.json()["status_rencana"] == "BELUM_DIRENCANAKAN"


def test_get_task_by_id_200_dan_404(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Detail Tugas",
            "matkul": "Manajemen Proyek",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    tugas_id = buat.json()["id"]

    resp_ok = client.get(f"/api/v1/tasks/{tugas_id}", headers=headers_a)
    assert resp_ok.status_code == 200
    assert resp_ok.json()["id"] == tugas_id
    assert resp_ok.json()["matkul"] == "Manajemen Proyek"

    resp_not_found = client.get("/api/v1/tasks/999999", headers=headers_a)
    assert resp_not_found.status_code == 404


def test_patch_task_status_sah_mengubah_nilai_dan_konsisten_di_get(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Selesaikan Modul",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    tugas_id = buat.json()["id"]

    resp_patch = client.patch(
        f"/api/v1/tasks/{tugas_id}",
        json={"status": "SELESAI"},
        headers=headers_a,
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["status"] == "SELESAI"
    assert resp_patch.json()["status_rencana"] == "BELUM_DIRENCANAKAN"

    resp_get = client.get(f"/api/v1/tasks/{tugas_id}", headers=headers_a)
    assert resp_get.status_code == 200
    assert resp_get.json()["status"] == "SELESAI"


def test_patch_task_status_tidak_sah_422_dan_id_tak_ada_404(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tes Validasi Patch",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    tugas_id = buat.json()["id"]

    resp_422 = client.patch(
        f"/api/v1/tasks/{tugas_id}",
        json={"status": "TERJADWAL"},
        headers=headers_a,
    )
    assert resp_422.status_code == 422

    resp_404 = client.patch(
        "/api/v1/tasks/999999",
        json={"status": "DIKERJAKAN"},
        headers=headers_a,
    )
    assert resp_404.status_code == 404


def test_semua_endpoint_tugas_tanpa_header_atau_token_salah_dijawab_401(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    buat = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Rahasia",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    tugas_id = buat.json()["id"]

    for headers_invalid in [{}, {"Authorization": "Bearer token_palsu"}]:
        r_post = client.post(
            "/api/v1/tasks",
            json={
                "judul": "Gagal",
                "jenis": JENIS_VALID,
                "bobot": 0.5,
                "tenggat": "2026-11-26T20:00:00",
            },
            headers=headers_invalid,
        )
        assert r_post.status_code == 401
        assert r_post.headers.get("WWW-Authenticate") == "Bearer"

        r_list = client.get("/api/v1/tasks", headers=headers_invalid)
        assert r_list.status_code == 401
        assert r_list.headers.get("WWW-Authenticate") == "Bearer"

        r_get = client.get(f"/api/v1/tasks/{tugas_id}", headers=headers_invalid)
        assert r_get.status_code == 401
        assert r_get.headers.get("WWW-Authenticate") == "Bearer"

        r_patch = client.patch(
            f"/api/v1/tasks/{tugas_id}",
            json={"status": "SELESAI"},
            headers=headers_invalid,
        )
        assert r_patch.status_code == 401
        assert r_patch.headers.get("WWW-Authenticate") == "Bearer"


def test_isolasi_tugas_antar_pengguna_get_list_dan_patch(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01", nama="Fikri")
    headers_b = buat_profil_dengan_token(client, user_id="u02", nama="Intan")

    resp_a = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Milik A",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_a,
    )
    tugas_a_id = resp_a.json()["id"]

    resp_b = client.post(
        "/api/v1/tasks",
        json={
            "judul": "Tugas Milik B",
            "jenis": JENIS_VALID,
            "bobot": 0.5,
            "tenggat": "2026-11-26T20:00:00",
        },
        headers=headers_b,
    )
    tugas_b_id = resp_b.json()["id"]

    # 1. GET /tasks milik A tidak memuat tugas B
    daftar_a = client.get("/api/v1/tasks", headers=headers_a).json()
    assert [t["id"] for t in daftar_a] == [tugas_a_id]

    # 2. User B tidak bisa GET tugas milik A -> 404
    resp_get_lintas = client.get(f"/api/v1/tasks/{tugas_a_id}", headers=headers_b)
    assert resp_get_lintas.status_code == 404

    # 3. User B tidak bisa PATCH tugas milik A -> 404, dan status tugas A tetap BARU
    resp_patch_lintas = client.patch(
        f"/api/v1/tasks/{tugas_a_id}",
        json={"status": "SELESAI"},
        headers=headers_b,
    )
    assert resp_patch_lintas.status_code == 404

    cek_a = client.get(f"/api/v1/tasks/{tugas_a_id}", headers=headers_a).json()
    assert cek_a["status"] == "BARU"
    assert tugas_b_id != tugas_a_id