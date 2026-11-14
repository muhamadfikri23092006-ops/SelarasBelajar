import math
from datetime import datetime, timedelta
import pytest

from services.tools.scheduler import hitung_menit_tersedia, schedule_blocks


BASE = datetime(2026, 11, 14, 8, 0)


def dt(menit_offset: int) -> datetime:
    return BASE + timedelta(minutes=menit_offset)


# ==========================================
# 1. KASUS UJI SPESIFIKASI & PEMBULATAN
# ==========================================

def test_satu_slot():
    hasil = hitung_menit_tersedia(
        slot_kosong=[(dt(0), dt(60))],
        tenggat=dt(240),
    )
    assert hasil == 60
    assert isinstance(hasil, int)


def test_dua_slot_terpisah():
    hasil = hitung_menit_tersedia(
        slot_kosong=[(dt(0), dt(60)), (dt(120), dt(180))],
        tenggat=dt(240),
    )
    assert hasil == 120


def test_dua_slot_tumpang_tindih():
    hasil = hitung_menit_tersedia(
        slot_kosong=[(dt(0), dt(90)), (dt(60), dt(120))],
        tenggat=dt(240),
    )
    assert hasil == 120


def test_slot_memotong_tenggat():
    hasil = hitung_menit_tersedia(
        slot_kosong=[(dt(0), dt(120))],
        tenggat=dt(90),
    )
    assert hasil == 90


def test_slot_setelah_tenggat():
    hasil = hitung_menit_tersedia(
        slot_kosong=[(dt(100), dt(160))],
        tenggat=dt(60),
    )
    assert hasil == 0


def test_daftar_slot_kosong():
    hasil = hitung_menit_tersedia(
        slot_kosong=[],
        tenggat=dt(240),
    )
    assert hasil == 0


def test_durasi_pecahan_dibulatkan_ke_bawah():
    # 90 detik = 1.5 menit -> math.floor menghasilkan 1
    hasil = hitung_menit_tersedia(
        slot_kosong=[(BASE, BASE + timedelta(seconds=90))],
        tenggat=dt(60),
    )
    assert hasil == 1
    assert isinstance(hasil, int)


# ==========================================
# 2. TES PENGHUBUNG: hitung_menit_tersedia == total schedule_blocks
# ==========================================

@pytest.mark.parametrize(
    "skenario, slot_kosong, tenggat",
    [
        (
            "satu_slot",
            [(dt(0), dt(60))],
            dt(240),
        ),
        (
            "dua_slot_terpisah",
            [(dt(0), dt(60)), (dt(120), dt(180))],
            dt(240),
        ),
        (
            "dua_slot_tumpang_tindih",
            [(dt(0), dt(90)), (dt(60), dt(120))],
            dt(240),
        ),
        (
            "slot_memotong_tenggat",
            [(dt(0), dt(120))],
            dt(90),
        ),
        (
            "slot_setelah_tenggat",
            [(dt(100), dt(160))],
            dt(60),
        ),
        (
            "campuran_tumpang_tindih_dan_potong_tenggat",
            [(dt(0), dt(75)), (dt(45), dt(150)), (dt(180), dt(240))],
            dt(120),
        ),
    ],
)
def test_penghubung_konsisten_dengan_schedule_blocks(skenario, slot_kosong, tenggat):
    menit_tersedia = hitung_menit_tersedia(
        slot_kosong=slot_kosong,
        tenggat=tenggat,
    )

    blok_terjadwal = schedule_blocks(
        estimasi_menit=100000,
        slot_kosong=slot_kosong,
        tenggat=tenggat,
        maks_blok_menit=60,
    )

    total_menit_terjadwal = math.floor(
        sum((selesai - mulai).total_seconds() / 60.0 for mulai, selesai in blok_terjadwal)
    )

    assert menit_tersedia == total_menit_terjadwal, f"Tidak sinkron pada skenario: {skenario}"