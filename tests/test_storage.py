from datetime import datetime

import pytest

from services.storage.db import (
    create_task,
    delete_profile,
    get_profile,
    get_task,
    init_db,
    list_tasks,
    save_blocks,
    save_profile,
    update_task_status,
)
from services.tools.effort import MENIT_DASAR

JENIS_VALID = next(iter(MENIT_DASAR.keys()))


# --- Tahap 9B: init_db ---


def test_init_db_membuat_tepat_tiga_tabel():
    koneksi = init_db(":memory:")
    baris = koneksi.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    nama_tabel = {r["name"] for r in baris}
    assert nama_tabel == {"profil", "tugas", "blok_jadwal"}


def test_init_db_idempoten_pada_berkas_sementara(tmp_path):
    db_file = tmp_path / "uji_idempoten.db"
    koneksi_1 = init_db(db_file)
    koneksi_1.close()

    koneksi_2 = init_db(db_file)
    baris = koneksi_2.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    assert {r["name"] for r in baris} == {"profil", "tugas", "blok_jadwal"}
    koneksi_2.close()


# --- Tahap 9C: profil & foreign key ---


def test_foreign_key_create_task_user_tak_terdaftar():
    koneksi = init_db()
    with pytest.raises(ValueError):
        create_task(
            koneksi,
            user_id="user_hantu",
            judul="Rangkuman Bab 1",
            jenis=JENIS_VALID,
            bobot=0.5,
            tenggat=datetime(2026, 11, 25, 23, 59),
        )


def test_save_dan_get_profile_mengembalikan_data_sama():
    koneksi = init_db()
    skor_awal = {"visual": 8, "aural": 5, "read_write": 7, "kinestetik": 4}
    save_profile(koneksi, user_id="u01", nama="Fikri", skor=skor_awal)

    profil = get_profile(koneksi, user_id="u01")
    assert profil is not None
    assert profil["user_id"] == "u01"
    assert profil["nama"] == "Fikri"
    assert profil["skor"] == skor_awal
    assert datetime.fromisoformat(profil["dibuat_pada"])


def test_save_profile_upsert_data_terbaru_menang():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Nama Lama",
        skor={"visual": 1, "aural": 1, "read_write": 1, "kinestetik": 1},
    )
    skor_baru = {"visual": 9, "aural": 6, "read_write": 8, "kinestetik": 7}
    save_profile(koneksi, user_id="u01", nama="Nama Baru", skor=skor_baru)

    profil = get_profile(koneksi, user_id="u01")
    assert profil is not None
    assert profil["nama"] == "Nama Baru"
    assert profil["skor"] == skor_baru


@pytest.mark.parametrize(
    "skor_invalid",
    [
        {"visual": -1, "aural": 5, "read_write": 5, "kinestetik": 5},
        {"visual": 5, "aural": 5, "read_write": 5},
        {"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5, "ekstra": 1},
    ],
)
def test_save_profile_skor_invalid_mengangkat_value_error(skor_invalid):
    koneksi = init_db()
    with pytest.raises(ValueError):
        save_profile(koneksi, user_id="u01", nama="Fikri", skor=skor_invalid)


def test_get_profile_user_tak_ada_mengembalikan_none():
    koneksi = init_db()
    assert get_profile(koneksi, user_id="tidak_ada") is None


# --- Tahap 9D: tugas & blok_jadwal ---


def test_create_task_valid_mengembalikan_id_dan_status_baru():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 7, "aural": 4, "read_write": 8, "kinestetik": 5},
    )
    tenggat = datetime(2026, 11, 25, 20, 0)
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Rangkuman Jaringan",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=tenggat,
    )

    assert isinstance(tugas_id, int)
    tugas = get_task(koneksi, tugas_id=tugas_id)
    assert tugas is not None
    assert tugas["status"] == "BARU"
    assert tugas["status_rencana"] == "BELUM_DIRENCANAKAN"
    assert tugas["tenggat"] == tenggat
    assert tugas["blok"] == []


@pytest.mark.parametrize(
    ("judul", "jenis", "bobot"),
    [
        ("Tugas Valid", JENIS_VALID, 1.5),
        ("Tugas Valid", JENIS_VALID, -0.1),
        ("Tugas Valid", "jenis_ngawur", 0.5),
        ("", JENIS_VALID, 0.5),
        ("   ", JENIS_VALID, 0.5),
    ],
)
def test_create_task_input_invalid_mengangkat_value_error(judul, jenis, bobot):
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    with pytest.raises(ValueError):
        create_task(
            koneksi,
            user_id="u01",
            judul=judul,
            jenis=jenis,
            bobot=bobot,
            tenggat=datetime(2026, 11, 25, 20, 0),
        )


def test_save_blocks_lalu_get_task_mengembalikan_tuple_datetime_terurut():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Latihan Keamanan",
        jenis=JENIS_VALID,
        bobot=0.6,
        tenggat=datetime(2026, 11, 26, 23, 59),
    )

    blok_kedua = (datetime(2026, 11, 21, 13, 0), datetime(2026, 11, 21, 14, 0))
    blok_pertama = (datetime(2026, 11, 20, 9, 0), datetime(2026, 11, 20, 10, 0))

    # Sengaja dimasukkan tidak berurutan untuk menguji pengurutan otomatis
    save_blocks(
        koneksi,
        tugas_id=tugas_id,
        blok=[blok_kedua, blok_pertama],
        status_rencana="TERJADWAL",
    )

    tugas = get_task(koneksi, tugas_id=tugas_id)
    assert tugas is not None
    assert tugas["status"] == "BARU"
    assert tugas["status_rencana"] == "TERJADWAL"
    assert tugas["blok"] == [blok_pertama, blok_kedua]


def test_save_blocks_dua_kali_hanya_blok_terbaru_tersisa():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Laporan Praktikum",
        jenis=JENIS_VALID,
        bobot=0.7,
        tenggat=datetime(2026, 11, 28, 23, 59),
    )

    blok_lama = [(datetime(2026, 11, 20, 8, 0), datetime(2026, 11, 20, 9, 0))]
    blok_baru = [(datetime(2026, 11, 22, 10, 0), datetime(2026, 11, 22, 11, 30))]

    save_blocks(koneksi, tugas_id=tugas_id, blok=blok_lama, status_rencana="TERJADWAL")
    save_blocks(koneksi, tugas_id=tugas_id, blok=blok_baru, status_rencana="TERJADWAL")

    tugas = get_task(koneksi, tugas_id=tugas_id)
    assert tugas is not None
    assert tugas["blok"] == blok_baru


def test_save_blocks_pada_tugas_id_tak_ada_mengangkat_value_error():
    koneksi = init_db()
    with pytest.raises(ValueError):
        save_blocks(
            koneksi,
            tugas_id=9999,
            blok=[(datetime(2026, 11, 20, 9, 0), datetime(2026, 11, 20, 10, 0))],
            status_rencana="TERJADWAL",
        )


def test_list_tasks_terurut_menurut_tenggat():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )

    id_jauh = create_task(
        koneksi,
        user_id="u01",
        judul="Tugas Akhir",
        jenis=JENIS_VALID,
        bobot=0.8,
        tenggat=datetime(2026, 12, 10, 23, 59),
    )
    id_dekat = create_task(
        koneksi,
        user_id="u01",
        judul="Kuis Harian",
        jenis=JENIS_VALID,
        bobot=0.2,
        tenggat=datetime(2026, 11, 20, 12, 0),
    )
    id_sedang = create_task(
        koneksi,
        user_id="u01",
        judul="Ringkasan Mingguan",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 25, 18, 0),
    )

    daftar = list_tasks(koneksi, user_id="u01")
    assert [t["id"] for t in daftar] == [id_dekat, id_sedang, id_jauh]


def test_save_profile_upsert_tidak_mengubah_dibuat_pada():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Nama Lama",
        skor={"visual": 1, "aural": 1, "read_write": 1, "kinestetik": 1},
    )
    profil_awal = get_profile(koneksi, user_id="u01")
    assert profil_awal is not None

    save_profile(
        koneksi,
        user_id="u01",
        nama="Nama Baru",
        skor={"visual": 9, "aural": 6, "read_write": 8, "kinestetik": 7},
    )
    profil_akhir = get_profile(koneksi, user_id="u01")
    assert profil_akhir is not None
    assert profil_akhir["dibuat_pada"] == profil_awal["dibuat_pada"]


# --- Tugas 11A: Skema dan Status ---


def test_create_task_matkul_default_dan_kustom():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tenggat = datetime(2026, 11, 27, 20, 0)

    id_tanpa_matkul = create_task(
        koneksi,
        user_id="u01",
        judul="Tugas Tanpa Matkul",
        jenis=JENIS_VALID,
        bobot=0.4,
        tenggat=tenggat,
    )
    id_dengan_matkul = create_task(
        koneksi,
        user_id="u01",
        judul="Analisis Wireshark",
        jenis=JENIS_VALID,
        bobot=0.6,
        tenggat=tenggat,
        matkul="Keamanan Informasi",
    )

    tugas_1 = get_task(koneksi, tugas_id=id_tanpa_matkul)
    tugas_2 = get_task(koneksi, tugas_id=id_dengan_matkul)
    assert tugas_1 is not None and tugas_1["matkul"] == ""
    assert tugas_2 is not None and tugas_2["matkul"] == "Keamanan Informasi"

    daftar = list_tasks(koneksi, user_id="u01")
    by_id = {t["id"]: t for t in daftar}
    assert by_id[id_tanpa_matkul]["matkul"] == ""
    assert by_id[id_dengan_matkul]["matkul"] == "Keamanan Informasi"


def test_create_task_status_pengerjaan_dan_rencana_awal():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Tugas Awal",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 27, 20, 0),
    )

    tugas = get_task(koneksi, tugas_id=tugas_id)
    assert tugas is not None
    assert tugas["status"] == "BARU"
    assert tugas["status_rencana"] == "BELUM_DIRENCANAKAN"


def test_save_blocks_hanya_mengubah_status_rencana_tidak_menyentuh_status():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Simulasi Jadwal",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 27, 20, 0),
    )

    save_blocks(
        koneksi,
        tugas_id=tugas_id,
        blok=[(datetime(2026, 11, 25, 9, 0), datetime(2026, 11, 25, 10, 0))],
        status_rencana="TERJADWAL",
    )

    tugas = get_task(koneksi, tugas_id=tugas_id)
    assert tugas is not None
    assert tugas["status"] == "BARU"
    assert tugas["status_rencana"] == "TERJADWAL"


@pytest.mark.parametrize("status_invalid", ["SELESAI", "ASAL"])
def test_save_blocks_status_rencana_tidak_valid_mengangkat_value_error(status_invalid):
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Latihan Validasi",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 26, 23, 59),
    )

    with pytest.raises(ValueError):
        save_blocks(
            koneksi,
            tugas_id=tugas_id,
            blok=[(datetime(2026, 11, 20, 9, 0), datetime(2026, 11, 20, 10, 0))],
            status_rencana=status_invalid,
        )


def test_delete_profile_menghapus_profil_tugas_dan_blok_secara_cascade():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Tugas Cascade",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 27, 20, 0),
        matkul="Manajemen Proyek",
    )
    save_blocks(
        koneksi,
        tugas_id=tugas_id,
        blok=[(datetime(2026, 11, 25, 10, 0), datetime(2026, 11, 25, 11, 0))],
        status_rencana="TERJADWAL",
    )

    terhapus = delete_profile(koneksi, user_id="u01")
    assert terhapus is True
    assert get_profile(koneksi, user_id="u01") is None
    assert get_task(koneksi, tugas_id=tugas_id) is None

    sisa_blok = koneksi.execute("SELECT COUNT(*) AS jumlah FROM blok_jadwal;").fetchone()
    assert sisa_blok["jumlah"] == 0


def test_delete_profile_user_tidak_ada_mengembalikan_false():
    koneksi = init_db()
    assert delete_profile(koneksi, user_id="user_tidak_ada") is False

# --- Tugas 11C: update_task_status ---


def test_update_task_status_mengubah_status_tanpa_mengubah_status_rencana():
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Implementasi API",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 27, 20, 0),
    )

    diubah = update_task_status(koneksi, tugas_id=tugas_id, status="DIKERJAKAN")
    assert diubah is True

    tugas = get_task(koneksi, tugas_id=tugas_id)
    assert tugas is not None
    assert tugas["status"] == "DIKERJAKAN"
    assert tugas["status_rencana"] == "BELUM_DIRENCANAKAN"


@pytest.mark.parametrize("status_tidak_sah", ["TERJADWAL", "ASAL"])
def test_update_task_status_tidak_sah_mengangkat_value_error(status_tidak_sah):
    koneksi = init_db()
    save_profile(
        koneksi,
        user_id="u01",
        nama="Fikri",
        skor={"visual": 5, "aural": 5, "read_write": 5, "kinestetik": 5},
    )
    tugas_id = create_task(
        koneksi,
        user_id="u01",
        judul="Validasi Status",
        jenis=JENIS_VALID,
        bobot=0.5,
        tenggat=datetime(2026, 11, 27, 20, 0),
    )

    with pytest.raises(ValueError):
        update_task_status(koneksi, tugas_id=tugas_id, status=status_tidak_sah)


def test_update_task_status_id_tak_ada_mengembalikan_false():
    koneksi = init_db()
    assert update_task_status(koneksi, tugas_id=9999, status="SELESAI") is False