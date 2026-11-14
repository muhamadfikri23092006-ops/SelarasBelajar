from datetime import datetime, timedelta
import pytest

from services.verifier.schedule_check import verify_schedule
from services.tools.scheduler import schedule_blocks


BASE = datetime(2026, 11, 14, 8, 0)


def dt(menit_offset: int) -> datetime:
    return BASE + timedelta(minutes=menit_offset)


# ==========================================
# 1. TES JADWAL VALID & KEPUTUSAN DESAIN
# ==========================================

def test_jadwal_valid():
    blok = [
        (dt(0), dt(45)),
        (dt(60), dt(105)),
    ]
    hasil = verify_schedule(
        blok=blok,
        tenggat=dt(120),
        maks_blok_menit=60,
        estimasi_menit=90,
    )
    assert hasil == {"valid": True, "pelanggaran": []}


def test_daftar_blok_kosong_valid():
    hasil = verify_schedule(
        blok=[],
        tenggat=dt(120),
        maks_blok_menit=60,
        estimasi_menit=90,
    )
    assert hasil == {"valid": True, "pelanggaran": []}


# ==========================================
# 2. SATU TES PER KODE PELANGGARAN (5 TES)
# ==========================================

def test_pelanggaran_blok_tidak_valid():
    blok = [
        (dt(60), dt(60)),  # mulai == selesai
        (dt(90), dt(70)),  # mulai > selesai
    ]
    hasil = verify_schedule(
        blok=blok,
        tenggat=dt(180),
        maks_blok_menit=60,
        estimasi_menit=120,
    )
    assert hasil["valid"] is False
    assert hasil["pelanggaran"] == ["BLOK_TIDAK_VALID"]


def test_pelanggaran_melewati_tenggat():
    blok = [
        (dt(0), dt(45)),
        (dt(60), dt(125)),  # selesai lewat tenggat dt(120)
    ]
    hasil = verify_schedule(
        blok=blok,
        tenggat=dt(120),
        maks_blok_menit=90,
        estimasi_menit=120,
    )
    assert hasil["valid"] is False
    assert hasil["pelanggaran"] == ["MELEWATI_TENGGAT"]


def test_pelanggaran_blok_terlalu_panjang():
    blok = [
        (dt(0), dt(75)),  # 75 menit > maks 60 menit
    ]
    hasil = verify_schedule(
        blok=blok,
        tenggat=dt(180),
        maks_blok_menit=60,
        estimasi_menit=120,
    )
    assert hasil["valid"] is False
    assert hasil["pelanggaran"] == ["BLOK_TERLALU_PANJANG"]


def test_pelanggaran_tumpang_tindih_dan_urutan_input_tidak_berubah():
    blok_awal = [
        (dt(30), dt(75)),
        (dt(0), dt(45)),  # tabrakan di menit 30..45
    ]
    salinan_pembanding = list(blok_awal)

    hasil = verify_schedule(
        blok=blok_awal,
        tenggat=dt(180),
        maks_blok_menit=60,
        estimasi_menit=120,
    )
    assert hasil["valid"] is False
    assert hasil["pelanggaran"] == ["TUMPANG_TINDIH"]
    assert blok_awal == salinan_pembanding


def test_pelanggaran_total_melebihi_estimasi():
    blok = [
        (dt(0), dt(50)),
        (dt(60), dt(110)),  # total 100 menit > estimasi 90 menit
    ]
    hasil = verify_schedule(
        blok=blok,
        tenggat=dt(180),
        maks_blok_menit=60,
        estimasi_menit=90,
    )
    assert hasil["valid"] is False
    assert hasil["pelanggaran"] == ["TOTAL_MELEBIHI_ESTIMASI"]


# ==========================================
# 3. DUA PELANGGARAN SEKALIGUS
# ==========================================

def test_dua_pelanggaran_sekaligus():
    blok = [
        (dt(0), dt(80)),    # 80 menit -> BLOK_TERLALU_PANJANG
        (dt(90), dt(140)),  # selesai 140 > 120 -> MELEWATI_TENGGAT
    ]
    hasil = verify_schedule(
        blok=blok,
        tenggat=dt(120),
        maks_blok_menit=60,
        estimasi_menit=150,
    )
    assert hasil["valid"] is False
    assert set(hasil["pelanggaran"]) == {"BLOK_TERLALU_PANJANG", "MELEWATI_TENGGAT"}
    assert len(hasil["pelanggaran"]) == 2


# ==========================================
# 4. TES INTEGRASI: schedule_blocks -> verify_schedule
# ==========================================

@pytest.mark.parametrize(
    "skenario, slot_tersedia, estimasi_menit, maks_blok_menit, tenggat",
    [
        (
            "satu_slot",
            [(dt(0), dt(180))],
            90,
            45,
            dt(240),
        ),
        (
            "dua_slot",
            [
                (dt(0), dt(60)),
                (dt(120), dt(240)),
            ],
            120,
            60,
            dt(300),
        ),
        (
            "slot_tumpang_tindih",
            [
                (dt(0), dt(90)),
                (dt(45), dt(135)),
            ],
            100,
            50,
            dt(240),
        ),
        (
            "waktu_tidak_cukup",
            [(dt(0), dt(40))],
            120,
            60,
            dt(240),
        ),
        (
            "slot_melewati_tenggat",
            [(dt(0), dt(180))],
            90,
            45,
            dt(60),
        ),
    ],
)
def test_integrasi_schedule_blocks_selalu_valid(
    skenario, slot_tersedia, estimasi_menit, maks_blok_menit, tenggat
):
    hasil_jadwal = schedule_blocks(
        estimasi_menit=estimasi_menit,
        slot_kosong=slot_tersedia,
        tenggat=tenggat,
        maks_blok_menit=maks_blok_menit,
    )

    verifikasi = verify_schedule(
        blok=hasil_jadwal,
        tenggat=tenggat,
        maks_blok_menit=maks_blok_menit,
        estimasi_menit=estimasi_menit,
    )
    assert verifikasi == {"valid": True, "pelanggaran": []}, f"Gagal pada skenario: {skenario}"