from fastapi.testclient import TestClient
from apps.api.main import app


client = TestClient(app)


def test_plan_valid():
    payload = {
        "jenis": "kuis",
        "bobot": 0.0,
        "slot_kosong": [
            {
                "mulai": "2026-11-14T08:00:00",
                "selesai": "2026-11-14T10:00:00",
            }
        ],
        "tenggat": "2026-11-14T12:00:00",
    }
    r = client.post("/api/v1/plan", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert data["status"] == "SELESAI"
    assert data["estimasi_menit"] == 60
    assert data["menit_tersedia"] == 120
    assert data["kecukupan"]["cukup"] is True
    assert data["verifikasi"] == {"valid": True, "pelanggaran": []}
    assert data["blok"] == [
        {
            "mulai": "2026-11-14T08:00:00",
            "selesai": "2026-11-14T09:00:00",
        }
    ]


def test_plan_waktu_tidak_cukup():
    # kuis bobot 0.0 butuh 60 menit, slot hanya 30 menit -> tetap 200 OK dengan status WAKTU_TIDAK_CUKUP
    payload = {
        "jenis": "kuis",
        "bobot": 0.0,
        "slot_kosong": [
            {
                "mulai": "2026-11-14T08:00:00",
                "selesai": "2026-11-14T08:30:00",
            }
        ],
        "tenggat": "2026-11-14T12:00:00",
    }
    r = client.post("/api/v1/plan", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert data["status"] == "WAKTU_TIDAK_CUKUP"
    assert data["kecukupan"]["cukup"] is False
    assert data["verifikasi"]["valid"] is True


def test_plan_jenis_tidak_dikenal():
    # ValueError dari plan_task harus dikonversi menjadi 422 dengan detail pesan yang jelas
    payload = {
        "jenis": "tugas_misterius",
        "bobot": 0.5,
        "slot_kosong": [
            {
                "mulai": "2026-11-14T08:00:00",
                "selesai": "2026-11-14T10:00:00",
            }
        ],
        "tenggat": "2026-11-14T12:00:00",
    }
    r = client.post("/api/v1/plan", json=payload)
    assert r.status_code == 422
    assert "detail" in r.json()


def test_plan_tanggal_salah_format():
    # Validasi otomatis Pydantic terhadap string tanggal tidak valid -> 422
    payload = {
        "jenis": "kuis",
        "bobot": 0.0,
        "slot_kosong": [
            {
                "mulai": "bukan-format-tanggal",
                "selesai": "2026-11-14T10:00:00",
            }
        ],
        "tenggat": "2026-11-14T12:00:00",
    }
    r = client.post("/api/v1/plan", json=payload)
    assert r.status_code == 422