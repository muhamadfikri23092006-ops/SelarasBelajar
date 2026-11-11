from datetime import datetime, timedelta
import pytest
from services.tools.scheduler import schedule_blocks


@pytest.fixture
def base_time():
    return datetime(2026, 11, 12, 10, 0)


def assert_sifat_jadwal(
    blok_list, tenggat, maks_blok_menit, total_estimasi_menit
):
    total_durasi = 0
    for i, (mulai, selesai) in enumerate(blok_list):
        durasi = (selesai - mulai).total_seconds() / 60
        assert selesai <= tenggat
        assert durasi <= maks_blok_menit
        if i > 0:
            mulai_prev, selesai_prev = blok_list[i - 1]
            assert mulai >= selesai_prev
        total_durasi += durasi
    assert total_durasi <= total_estimasi_menit


def test_satu_slot_cukup(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(minutes=45))]

    hasil = schedule_blocks(
        estimasi_menit=45, slot_kosong=slot_kosong, tenggat=tenggat
    )

    assert len(hasil) == 1
    assert hasil[0] == (base_time, base_time + timedelta(minutes=45))
    assert_sifat_jadwal(hasil, tenggat, 60, 45)


def test_slot_panjang_dipecah(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(minutes=150))]

    hasil = schedule_blocks(
        estimasi_menit=150,
        slot_kosong=slot_kosong,
        tenggat=tenggat,
        maks_blok_menit=60,
    )

    assert len(hasil) == 3
    assert_sifat_jadwal(hasil, tenggat, 60, 150)


def test_slot_melewati_tenggat(base_time):
    tenggat = base_time + timedelta(minutes=90)
    slot_kosong = [(base_time, base_time + timedelta(minutes=120))]

    hasil = schedule_blocks(
        estimasi_menit=120, slot_kosong=slot_kosong, tenggat=tenggat
    )

    assert len(hasil) == 2
    assert_sifat_jadwal(hasil, tenggat, 60, 120)


def test_dua_slot(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [
        (base_time, base_time + timedelta(minutes=30)),
        (base_time + timedelta(hours=1), base_time + timedelta(hours=1, minutes=40)),
    ]

    hasil = schedule_blocks(
        estimasi_menit=60, slot_kosong=slot_kosong, tenggat=tenggat
    )

    assert len(hasil) == 2
    assert_sifat_jadwal(hasil, tenggat, 60, 60)


def test_waktu_tidak_cukup(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(minutes=30))]

    hasil = schedule_blocks(
        estimasi_menit=90, slot_kosong=slot_kosong, tenggat=tenggat
    )

    assert len(hasil) == 1
    assert_sifat_jadwal(hasil, tenggat, 60, 90)


def test_maks_blok_menit_nol_atau_negatif(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(hours=2))]

    with pytest.raises(ValueError):
        schedule_blocks(
            estimasi_menit=60,
            slot_kosong=slot_kosong,
            tenggat=tenggat,
            maks_blok_menit=0,
        )

    with pytest.raises(ValueError):
        schedule_blocks(
            estimasi_menit=60,
            slot_kosong=slot_kosong,
            tenggat=tenggat,
            maks_blok_menit=-15,
        )


def test_slot_tumpang_tindih(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [
        (base_time, base_time + timedelta(minutes=90)),
        (base_time + timedelta(minutes=60), base_time + timedelta(minutes=120)),
    ]

    hasil = schedule_blocks(
        estimasi_menit=120, slot_kosong=slot_kosong, tenggat=tenggat
    )

    assert_sifat_jadwal(hasil, tenggat, 60, 120)
    total_durasi = sum(
        (selesai - mulai).total_seconds() / 60 for mulai, selesai in hasil
    )
    assert total_durasi == 120


def test_estimasi_menit_negatif(base_time):
    tenggat = base_time + timedelta(hours=5)
    slot_kosong = [(base_time, base_time + timedelta(hours=2))]

    with pytest.raises(ValueError):
        schedule_blocks(
            estimasi_menit=-30, slot_kosong=slot_kosong, tenggat=tenggat
        )