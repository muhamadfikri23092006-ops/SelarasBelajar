from datetime import datetime, timedelta
import pytest
from services.tools.scheduler import susun_jadwal


@pytest.fixture
def base_time():
    return datetime(2026, 11, 12, 10, 0)


def assert_sifat_jadwal(
    blok_list, tenggat, maks_blok_menit, total_estimasi_menit
):
    """Fungsi pembantu untuk memverifikasi 4 sifat wajib scheduler."""
    total_durasi = 0
    for i, (mulai, selesai) in enumerate(blok_list):
        durasi = (selesai - mulai).total_seconds() / 60

        # Sifat 1: Tidak ada blok yang berakhir setelah tenggat
        assert selesai <= tenggat

        # Sifat 3: Tidak ada blok lebih panjang dari maks_blok_menit
        assert durasi <= maks_blok_menit

        # Sifat 2: Tidak ada dua blok yang tumpang tindih (urutan sekuensial)
        if i > 0:
            mulai_prev, selesai_prev = blok_list[i - 1]
            assert mulai >= selesai_prev

        total_durasi += durasi

    # Sifat 4: Total durasi blok tidak melebihi estimasi_menit
    assert total_durasi <= total_estimasi_menit


def test_satu_slot_cukup(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(minutes=45))]

    hasil = susun_jadwal(
        estimasi_menit=45, slot_kosong=slot_kosong, tenggat=tenggat
    )

    assert len(hasil) == 1
    assert hasil[0] == (base_time, base_time + timedelta(minutes=45))
    assert_sifat_jadwal(hasil, tenggat, 60, 45)


def test_slot_panjang_dipecah(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(minutes=150))]

    hasil = susun_jadwal(
        estimasi_menit=150,
        slot_kosong=slot_kosong,
        tenggat=tenggat,
        maks_blok_menit=60,
    )

    # 150 menit dipecah menjadi 60 + 60 + 30
    assert len(hasil) == 3
    assert hasil[0] == (base_time, base_time + timedelta(minutes=60))
    assert hasil[1] == (
        base_time + timedelta(minutes=60),
        base_time + timedelta(minutes=120),
    )
    assert hasil[2] == (
        base_time + timedelta(minutes=120),
        base_time + timedelta(minutes=150),
    )
    assert_sifat_jadwal(hasil, tenggat, 60, 150)


def test_slot_melewati_tenggat(base_time):
    tenggat = base_time + timedelta(minutes=90)
    # Slot 120 menit, tetapi dipotong tenggat di 90 menit
    slot_kosong = [(base_time, base_time + timedelta(minutes=120))]

    hasil = susun_jadwal(
        estimasi_menit=120, slot_kosong=slot_kosong, tenggat=tenggat
    )

    # Hanya 90 menit pertama yang terpakai (60 + 30)
    assert len(hasil) == 2
    assert_sifat_jadwal(hasil, tenggat, 60, 120)
    total_durasi = sum(
        (selesai - mulai).total_seconds() / 60 for mulai, selesai in hasil
    )
    assert total_durasi == 90


def test_dua_slot(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [
        (base_time, base_time + timedelta(minutes=30)),
        (base_time + timedelta(hours=1), base_time + timedelta(hours=1, minutes=40)),
    ]

    hasil = susun_jadwal(
        estimasi_menit=60, slot_kosong=slot_kosong, tenggat=tenggat
    )

    # Memakai slot 1 (30 menit) + slot 2 (30 menit)
    assert len(hasil) == 2
    assert hasil[0] == (base_time, base_time + timedelta(minutes=30))
    assert hasil[1] == (
        base_time + timedelta(hours=1),
        base_time + timedelta(hours=1, minutes=30),
    )
    assert_sifat_jadwal(hasil, tenggat, 60, 60)


def test_waktu_tidak_cukup(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(minutes=30))]

    hasil = susun_jadwal(
        estimasi_menit=90, slot_kosong=slot_kosong, tenggat=tenggat
    )

    # Hanya bisa mengisi 30 menit dari 90 menit yang dibutuhkan
    assert len(hasil) == 1
    assert hasil[0] == (base_time, base_time + timedelta(minutes=30))
    assert_sifat_jadwal(hasil, tenggat, 60, 90)