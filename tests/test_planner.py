from datetime import datetime, timedelta
import pytest

from services.agent.planner import plan_task
from services.storage.db import VALID_STATUS_RENCANA


BASE = datetime(2026, 11, 14, 8, 0)


def dt(n: int) -> datetime:
    return BASE + timedelta(minutes=n)


def test_waktu_cukup():
    hasil = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(120))],
        tenggat=dt(240),
    )
    assert hasil["status"] == "TERJADWAL"
    assert hasil["estimasi_menit"] == 60
    assert hasil["menit_tersedia"] == 120
    assert hasil["kecukupan"]["cukup"] is True
    assert hasil["verifikasi"] == {"valid": True, "pelanggaran": []}

    total_durasi_blok = sum(
        (selesai - mulai).total_seconds() / 60.0
        for mulai, selesai in hasil["blok"]
    )
    assert total_durasi_blok == 60


def test_waktu_tidak_cukup():
    # kuis bobot 0.0 = 60 menit, sedangkan slot cuma 30 menit
    hasil = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(30))],
        tenggat=dt(240),
    )
    assert hasil["status"] == "WAKTU_TIDAK_CUKUP"
    assert hasil["estimasi_menit"] == 60
    assert hasil["menit_tersedia"] == 30
    assert hasil["kecukupan"]["cukup"] is False
    # Blok tetap valid (mengisi semampunya 30 menit tanpa melanggar aturan)
    assert hasil["verifikasi"]["valid"] is True


def test_tenggat_sebelum_slot():
    # Semua slot berada setelah tenggat -> menit_tersedia = 0 -> WAKTU_TIDAK_CUKUP
    hasil = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(120), dt(240))],
        tenggat=dt(60),
    )
    assert hasil["status"] == "WAKTU_TIDAK_CUKUP"
    assert hasil["menit_tersedia"] == 0
    assert hasil["blok"] == []
    assert hasil["verifikasi"]["valid"] is True


def test_jenis_tidak_dikenal():
    with pytest.raises(ValueError):
        plan_task(
            jenis="jenis_ngawur",
            bobot=0.5,
            slot_kosong=[(dt(0), dt(120))],
            tenggat=dt(240),
        )


def test_gagal_verifikasi_prioritas_tertinggi(monkeypatch):
    # Simulasikan schedule_blocks nakal yang menghasilkan blok melewati tenggat
    def schedule_blocks_rusak(**kwargs):
        return [(dt(0), dt(500))]

    monkeypatch.setattr(
        "services.agent.planner.schedule_blocks",
        schedule_blocks_rusak,
    )

    # Meskipun slot kosong sebenarnya tidak cukup (hanya 20 menit vs estimasi 60 menit),
    # status HARUS "GAGAL_VERIFIKASI", bukan "WAKTU_TIDAK_CUKUP".
    hasil = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(20))],
        tenggat=dt(60),
    )
    assert hasil["status"] == "GAGAL_VERIFIKASI"
    assert hasil["verifikasi"]["valid"] is False
    assert "MELEWATI_TENGGAT" in hasil["verifikasi"]["pelanggaran"]


def test_batas_pas_menit_tersedia_sama_dengan_estimasi():
    # kuis bobot 0.0 -> estimasi 60 menit; slot tersedia pas 60 menit -> TERJADWAL
    hasil = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(60))],
        tenggat=dt(240),
    )
    assert hasil["status"] == "TERJADWAL"
    assert hasil["estimasi_menit"] == 60
    assert hasil["menit_tersedia"] == 60
    assert hasil["kecukupan"]["cukup"] is True
    assert hasil["verifikasi"] == {"valid": True, "pelanggaran": []}


@pytest.mark.parametrize("bobot_tidak_valid", [-0.1, 1.5])
def test_bobot_di_luar_rentang_merambat_value_error(bobot_tidak_valid):
    with pytest.raises(ValueError):
        plan_task(
            jenis="kuis",
            bobot=bobot_tidak_valid,
            slot_kosong=[(dt(0), dt(120))],
            tenggat=dt(240),
        )


# --- Tugas 11B: Dasar Perhitungan (FR-05) & Kontrak Status ---


def test_plan_task_rangkuman_menyertakan_dasar_perhitungan():
    hasil = plan_task(
        jenis="rangkuman",
        bobot=0.5,
        slot_kosong=[(dt(0), dt(180))],
        tenggat=dt(240),
    )
    assert hasil["estimasi_menit"] == 135
    assert hasil["dasar"] == {"menit_dasar": 90, "bobot": 0.5}


def test_penjaga_kontrak_status_planner_ada_di_valid_status_rencana(monkeypatch):
    # 1. Skenario cukup -> TERJADWAL
    hasil_cukup = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(120))],
        tenggat=dt(240),
    )
    assert hasil_cukup["status"] in VALID_STATUS_RENCANA

    # 2. Skenario tidak cukup -> WAKTU_TIDAK_CUKUP
    hasil_kurang = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(30))],
        tenggat=dt(240),
    )
    assert hasil_kurang["status"] in VALID_STATUS_RENCANA

    # 3. Skenario gagal verifikasi -> GAGAL_VERIFIKASI
    monkeypatch.setattr(
        "services.agent.planner.schedule_blocks",
        lambda **kwargs: [(dt(0), dt(500))],
    )
    hasil_gagal = plan_task(
        jenis="kuis",
        bobot=0.0,
        slot_kosong=[(dt(0), dt(120))],
        tenggat=dt(60),
    )
    assert hasil_gagal["status"] in VALID_STATUS_RENCANA