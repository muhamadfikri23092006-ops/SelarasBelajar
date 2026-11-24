from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from services.tools.effort import MENIT_DASAR

_KUNCI_VARK = frozenset({"visual", "aural", "read_write", "kinestetik"})

STATUS_PENGERJAAN_DEFAULT = "BARU"
VALID_STATUS_TUGAS = frozenset({"BARU", "DIKERJAKAN", "SELESAI"})

STATUS_RENCANA_DEFAULT = "BELUM_DIRENCANAKAN"
VALID_STATUS_RENCANA = frozenset(
    {
        "BELUM_DIRENCANAKAN",
        "TERJADWAL",
        "WAKTU_TIDAK_CUKUP",
        "GAGAL_VERIFIKASI",
    }
)


def init_db(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Inisialisasi koneksi SQLite dan membuat skema 3 tabel secara idempoten."""
    koneksi = sqlite3.connect(str(path))
    koneksi.row_factory = sqlite3.Row
    koneksi.execute("PRAGMA foreign_keys = ON;")

    with koneksi:
        koneksi.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS profil (
                user_id TEXT PRIMARY KEY,
                nama TEXT NOT NULL,
                skor_visual INTEGER NOT NULL,
                skor_aural INTEGER NOT NULL,
                skor_read_write INTEGER NOT NULL,
                skor_kinestetik INTEGER NOT NULL,
                dibuat_pada TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tugas (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                judul TEXT NOT NULL,
                matkul TEXT NOT NULL DEFAULT '',
                jenis TEXT NOT NULL,
                bobot REAL NOT NULL,
                tenggat TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '{STATUS_PENGERJAAN_DEFAULT}',
                status_rencana TEXT NOT NULL DEFAULT '{STATUS_RENCANA_DEFAULT}',
                FOREIGN KEY (user_id) REFERENCES profil(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS blok_jadwal (
                id INTEGER PRIMARY KEY,
                tugas_id INTEGER NOT NULL,
                mulai TEXT NOT NULL,
                selesai TEXT NOT NULL,
                FOREIGN KEY (tugas_id) REFERENCES tugas(id) ON DELETE CASCADE
            );
            """
        )

    return koneksi


def save_profile(
    koneksi: sqlite3.Connection,
    *,
    user_id: str,
    nama: str,
    skor: dict[str, int],
) -> None:
    """Menyimpan atau memperbarui (upsert) profil VARK tanpa menimpa dibuat_pada."""
    if not user_id or not user_id.strip():
        raise ValueError("user_id tidak boleh kosong.")
    if not nama or not nama.strip():
        raise ValueError("nama tidak boleh kosong.")
    if not isinstance(skor, dict) or set(skor.keys()) != _KUNCI_VARK:
        raise ValueError(
            "skor harus memiliki tepat 4 kunci: visual, aural, read_write, kinestetik."
        )

    for kunci, nilai in skor.items():
        if isinstance(nilai, bool) or not isinstance(nilai, int) or nilai < 0:
            raise ValueError(f"Nilai skor '{kunci}' harus integer non-negatif.")

    dibuat_pada_iso = datetime.now().isoformat()

    with koneksi:
        koneksi.execute(
            """
            INSERT INTO profil (
                user_id, nama, skor_visual, skor_aural,
                skor_read_write, skor_kinestetik, dibuat_pada
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                nama = excluded.nama,
                skor_visual = excluded.skor_visual,
                skor_aural = excluded.skor_aural,
                skor_read_write = excluded.skor_read_write,
                skor_kinestetik = excluded.skor_kinestetik;
            """,
            (
                user_id.strip(),
                nama.strip(),
                skor["visual"],
                skor["aural"],
                skor["read_write"],
                skor["kinestetik"],
                dibuat_pada_iso,
            ),
        )


def get_profile(koneksi: sqlite3.Connection, *, user_id: str) -> dict[str, Any] | None:
    """Mengambil profil pengguna berdasarkan user_id, atau None jika tidak ada."""
    baris = koneksi.execute(
        """
        SELECT user_id, nama, skor_visual, skor_aural,
               skor_read_write, skor_kinestetik, dibuat_pada
        FROM profil
        WHERE user_id = ?;
        """,
        (user_id,),
    ).fetchone()

    if baris is None:
        return None

    return {
        "user_id": baris["user_id"],
        "nama": baris["nama"],
        "skor": {
            "visual": baris["skor_visual"],
            "aural": baris["skor_aural"],
            "read_write": baris["skor_read_write"],
            "kinestetik": baris["skor_kinestetik"],
        },
        "dibuat_pada": baris["dibuat_pada"],
    }


def delete_profile(koneksi: sqlite3.Connection, *, user_id: str) -> bool:
    """Menghapus profil beserta seluruh tugas dan blok jadwalnya secara cascade."""
    with koneksi:
        kursor = koneksi.execute(
            "DELETE FROM profil WHERE user_id = ?;",
            (user_id,),
        )
    return kursor.rowcount > 0


def create_task(
    koneksi: sqlite3.Connection,
    *,
    user_id: str,
    judul: str,
    jenis: str,
    bobot: float,
    tenggat: datetime,
    matkul: str = "",
) -> int:
    """Membuat tugas baru berstatus 'BARU' dan status_rencana 'BELUM_DIRENCANAKAN'."""
    if not judul or not judul.strip():
        raise ValueError("Judul tugas tidak boleh kosong.")
    if jenis not in MENIT_DASAR:
        raise ValueError(f"Jenis tugas '{jenis}' tidak dikenali dalam MENIT_DASAR.")
    if (
        isinstance(bobot, bool)
        or not isinstance(bobot, (int, float))
        or not (0.0 <= float(bobot) <= 1.0)
    ):
        raise ValueError("Bobot tugas harus berada di antara 0 dan 1.")
    if not isinstance(tenggat, datetime):
        raise ValueError("tenggat harus bertipe datetime.")
    if not isinstance(matkul, str):
        raise ValueError("matkul harus bertipe str.")

    with koneksi:
        cek_profil = koneksi.execute(
            "SELECT 1 FROM profil WHERE user_id = ?;",
            (user_id,),
        ).fetchone()
        if cek_profil is None:
            raise ValueError(f"user_id '{user_id}' tidak terdaftar.")

        kursor = koneksi.execute(
            """
            INSERT INTO tugas (
                user_id, judul, matkul, jenis, bobot, tenggat, status, status_rencana
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                user_id,
                judul.strip(),
                matkul.strip(),
                jenis,
                float(bobot),
                tenggat.isoformat(),
                STATUS_PENGERJAAN_DEFAULT,
                STATUS_RENCANA_DEFAULT,
            ),
        )

    return int(kursor.lastrowid)


def save_blocks(
    koneksi: sqlite3.Connection,
    *,
    tugas_id: int,
    blok: list[tuple[datetime, datetime]],
    status_rencana: str,
) -> None:
    """Mengganti seluruh blok jadwal milik tugas_id dan memperbarui status_rencana secara atomik."""
    if status_rencana not in VALID_STATUS_RENCANA:
        raise ValueError(
            f"status_rencana '{status_rencana}' tidak valid. "
            f"Harus salah satu dari {sorted(VALID_STATUS_RENCANA)}."
        )

    for mulai, selesai in blok:
        if not isinstance(mulai, datetime) or not isinstance(selesai, datetime):
            raise ValueError("Setiap blok harus berisi pasangan (datetime, datetime).")
        if selesai <= mulai:
            raise ValueError("Waktu selesai blok harus setelah waktu mulai.")

    with koneksi:
        cek_tugas = koneksi.execute(
            "SELECT 1 FROM tugas WHERE id = ?;",
            (tugas_id,),
        ).fetchone()
        if cek_tugas is None:
            raise ValueError(f"tugas_id {tugas_id} tidak ditemukan.")

        koneksi.execute(
            "DELETE FROM blok_jadwal WHERE tugas_id = ?;",
            (tugas_id,),
        )

        if blok:
            koneksi.executemany(
                """
                INSERT INTO blok_jadwal (tugas_id, mulai, selesai)
                VALUES (?, ?, ?);
                """,
                [
                    (tugas_id, mulai.isoformat(), selesai.isoformat())
                    for mulai, selesai in blok
                ],
            )

        koneksi.execute(
            "UPDATE tugas SET status_rencana = ? WHERE id = ?;",
            (status_rencana, tugas_id),
        )


def _ambil_blok_terurut(
    koneksi: sqlite3.Connection, tugas_id: int
) -> list[tuple[datetime, datetime]]:
    """Membaca daftar blok_jadwal milik suatu tugas dan mengonversi teks ISO ke datetime terurut."""
    baris_blok = koneksi.execute(
        """
        SELECT mulai, selesai
        FROM blok_jadwal
        WHERE tugas_id = ?;
        """,
        (tugas_id,),
    ).fetchall()

    hasil = [
        (datetime.fromisoformat(b["mulai"]), datetime.fromisoformat(b["selesai"]))
        for b in baris_blok
    ]
    hasil.sort(key=lambda item: item[0])
    return hasil


def _baris_ke_tugas(
    koneksi: sqlite3.Connection, baris: sqlite3.Row
) -> dict[str, Any]:
    """Mengonversi satu baris SQLite tabel tugas menjadi dictionary domain lengkap."""
    return {
        "id": baris["id"],
        "user_id": baris["user_id"],
        "judul": baris["judul"],
        "matkul": baris["matkul"],
        "jenis": baris["jenis"],
        "bobot": baris["bobot"],
        "tenggat": datetime.fromisoformat(baris["tenggat"]),
        "status": baris["status"],
        "status_rencana": baris["status_rencana"],
        "blok": _ambil_blok_terurut(koneksi, baris["id"]),
    }


def get_task(koneksi: sqlite3.Connection, *, tugas_id: int) -> dict[str, Any] | None:
    """Mengambil detail tugas beserta list tuple blok jadwal (datetime, datetime) terurut."""
    baris = koneksi.execute(
        """
        SELECT id, user_id, judul, matkul, jenis, bobot, tenggat, status, status_rencana
        FROM tugas
        WHERE id = ?;
        """,
        (tugas_id,),
    ).fetchone()

    if baris is None:
        return None

    return _baris_ke_tugas(koneksi, baris)


def list_tasks(koneksi: sqlite3.Connection, *, user_id: str) -> list[dict[str, Any]]:
    """Mengambil seluruh tugas milik user_id terurut dari tenggat paling dekat."""
    semua_baris = koneksi.execute(
        """
        SELECT id, user_id, judul, matkul, jenis, bobot, tenggat, status, status_rencana
        FROM tugas
        WHERE user_id = ?;
        """,
        (user_id,),
    ).fetchall()

    daftar = [_baris_ke_tugas(koneksi, b) for b in semua_baris]
    daftar.sort(key=lambda t: t["tenggat"])
    return daftar