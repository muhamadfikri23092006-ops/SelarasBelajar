from services.tools.effort import MENIT_DASAR
from tests.conftest import buat_profil_dengan_token

JENIS_VALID = next(iter(MENIT_DASAR.keys()))


def _buat_tugas_contoh(client, headers: dict[str, str], **override) -> dict:
    payload = {
        "judul": "Rangkuman Arsitektur",
        "matkul": "Keamanan Informasi",
        "jenis": JENIS_VALID,
        "bobot": 0.0,
        "tenggat": "2026-11-26T20:00:00",
        **override,
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def test_preview_dan_confirm_tanpa_token_atau_token_salah_401(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a)
    tid = tugas["id"]

    body = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }

    for headers_invalid in [{}, {"Authorization": "Bearer token_palsu"}]:
        r_prev = client.post(
            f"/api/v1/tasks/{tid}/plan/preview",
            json=body,
            headers=headers_invalid,
        )
        assert r_prev.status_code == 401
        assert r_prev.headers.get("WWW-Authenticate") == "Bearer"

        r_conf = client.post(
            f"/api/v1/tasks/{tid}/plan/confirm",
            json=body,
            headers=headers_invalid,
        )
        assert r_conf.status_code == 401
        assert r_conf.headers.get("WWW-Authenticate") == "Bearer"


def test_preview_dan_confirm_tugas_user_lain_404_dan_db_tidak_berubah(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01", nama="Fikri")
    headers_b = buat_profil_dengan_token(client, user_id="u02", nama="Intan")
    tugas_a = _buat_tugas_contoh(client, headers_a)
    tid = tugas_a["id"]

    body = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }

    r_prev = client.post(
        f"/api/v1/tasks/{tid}/plan/preview",
        json=body,
        headers=headers_b,
    )
    assert r_prev.status_code == 404

    r_conf = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body,
        headers=headers_b,
    )
    assert r_conf.status_code == 404

    # Pastikan tugas milik A tidak berubah di DB
    cek_a = client.get(f"/api/v1/tasks/{tid}", headers=headers_a).json()
    assert cek_a["status_rencana"] == "BELUM_DIRENCANAKAN"
    assert cek_a["blok"] == []


def test_preview_sukses_tidak_menyimpan_ke_db(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a)
    tid = tugas["id"]

    body = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }

    r_prev = client.post(
        f"/api/v1/tasks/{tid}/plan/preview",
        json=body,
        headers=headers_a,
    )
    assert r_prev.status_code == 200
    data_prev = r_prev.json()
    assert data_prev["status"] == "TERJADWAL"
    assert len(data_prev["blok"]) > 0
    assert "dasar" in data_prev

    # GET sesudahnya harus tetap kosong & BELUM_DIRENCANAKAN
    r_get = client.get(f"/api/v1/tasks/{tid}", headers=headers_a)
    assert r_get.status_code == 200
    data_get = r_get.json()
    assert data_get["blok"] == []
    assert data_get["status_rencana"] == "BELUM_DIRENCANAKAN"


def test_confirm_sukses_menyimpan_blok_dan_konsisten_di_get(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a)
    tid = tugas["id"]

    body = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }

    r_conf = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body,
        headers=headers_a,
    )
    assert r_conf.status_code == 200
    data_conf = r_conf.json()
    assert data_conf["id"] == tid
    assert data_conf["status_rencana"] == "TERJADWAL"
    assert data_conf["status"] == "BARU"
    assert len(data_conf["blok"]) > 0

    r_get = client.get(f"/api/v1/tasks/{tid}", headers=headers_a)
    assert r_get.status_code == 200
    data_get = r_get.json()
    assert data_get["status_rencana"] == "TERJADWAL"
    assert data_get["blok"] == data_conf["blok"]


def test_confirm_waktu_tidak_cukup_409_dan_db_tidak_berubah(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    # kuis bobot 0.0 butuh 60 menit; slot hanya 15 menit -> WAKTU_TIDAK_CUKUP -> 409
    tugas = _buat_tugas_contoh(client, headers_a, jenis="kuis", bobot=0.0)
    tid = tugas["id"]

    body = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T08:15:00",
            }
        ]
    }

    r_conf = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body,
        headers=headers_a,
    )
    assert r_conf.status_code == 409
    assert "detail" in r_conf.json()

    r_get = client.get(f"/api/v1/tasks/{tid}", headers=headers_a).json()
    assert r_get["status_rencana"] == "BELUM_DIRENCANAKAN"
    assert r_get["blok"] == []


def test_confirm_tugas_selesai_409(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a)
    tid = tugas["id"]

    # Ubah status pengerjaan tugas menjadi SELESAI
    r_patch = client.patch(
        f"/api/v1/tasks/{tid}",
        json={"status": "SELESAI"},
        headers=headers_a,
    )
    assert r_patch.status_code == 200

    body = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }

    r_conf = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body,
        headers=headers_a,
    )
    assert r_conf.status_code == 409
    assert "detail" in r_conf.json()


def test_confirm_dua_kali_mengganti_blok_tidak_menumpuk(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a, jenis="kuis", bobot=0.0)
    tid = tugas["id"]

    body_pertama = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }
    body_kedua = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T13:00:00",
                "selesai": "2026-11-25T15:00:00",
            }
        ]
    }

    r1 = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body_pertama,
        headers=headers_a,
    )
    assert r1.status_code == 200
    assert len(r1.json()["blok"]) == 1

    r2 = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body_kedua,
        headers=headers_a,
    )
    assert r2.status_code == 200
    blok_akhir = r2.json()["blok"]
    assert len(blok_akhir) == 1
    assert blok_akhir[0]["mulai"] == "2026-11-25T13:00:00"

    r_get = client.get(f"/api/v1/tasks/{tid}", headers=headers_a).json()
    assert r_get["blok"] == blok_akhir


def test_preview_dan_confirm_slot_tidak_valid_422(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a)
    tid = tugas["id"]

    # 1. Nilai maks_blok_menit <= 0 memicu ValueError dari plan_task -> 422
    body_maks_invalid = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ],
        "maks_blok_menit": 0,
    }

    r_prev = client.post(
        f"/api/v1/tasks/{tid}/plan/preview",
        json=body_maks_invalid,
        headers=headers_a,
    )
    assert r_prev.status_code == 422

    r_conf = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body_maks_invalid,
        headers=headers_a,
    )
    assert r_conf.status_code == 422

    # 2. Format tanggal slot tidak valid -> Pydantic 422
    body_tanggal_invalid = {
        "slot_kosong": [
            {
                "mulai": "bukan-format-tanggal",
                "selesai": "2026-11-25T10:00:00",
            }
        ]
    }

    assert (
        client.post(
            f"/api/v1/tasks/{tid}/plan/preview",
            json=body_tanggal_invalid,
            headers=headers_a,
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/tasks/{tid}/plan/confirm",
            json=body_tanggal_invalid,
            headers=headers_a,
        ).status_code
        == 422
    )


def test_preview_dan_confirm_body_menyertakan_blok_422(client):
    headers_a = buat_profil_dengan_token(client, user_id="u01")
    tugas = _buat_tugas_contoh(client, headers_a)
    tid = tugas["id"]

    body_dengan_blok = {
        "slot_kosong": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T10:00:00",
            }
        ],
        "blok": [
            {
                "mulai": "2026-11-25T08:00:00",
                "selesai": "2026-11-25T09:00:00",
            }
        ],
    }

    r_prev = client.post(
        f"/api/v1/tasks/{tid}/plan/preview",
        json=body_dengan_blok,
        headers=headers_a,
    )
    assert r_prev.status_code == 422

    r_conf = client.post(
        f"/api/v1/tasks/{tid}/plan/confirm",
        json=body_dengan_blok,
        headers=headers_a,
    )
    assert r_conf.status_code == 422