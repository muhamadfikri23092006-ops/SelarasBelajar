from datetime import datetime, timedelta


def susun_jadwal(
    estimasi_menit: int,
    slot_kosong: list[tuple[datetime, datetime]],
    tenggat: datetime,
    maks_blok_menit: int = 60,
) -> list[tuple[datetime, datetime]]:
    """Menyusun alokasi blok waktu kerja berdasarkan slot kosong dan tenggat.

    Aturan:
    1. Isi dari slot paling awal.
    2. Bagian slot yang melewati tenggat dipotong.
    3. Blok dipecah per maksimal maks_blok_menit.
    4. Berhenti setelah total durasi mencapai estimasi_menit.
    5. Mengembalikan blok yang berhasil dialokasikan meskipun waktu tidak cukup.
    """
    if estimasi_menit <= 0 or not slot_kosong:
        return []

    # Urutkan slot berdasarkan waktu mulai
    slot_terurut = sorted(slot_kosong, key=lambda x: x[0])
    sisa_estimasi = float(estimasi_menit)
    blok_jadwal = []

    for mulai, selesai in slot_terurut:
        if sisa_estimasi <= 0:
            break

        # Aturan 2: Potong slot di tenggat
        selesai_efektif = min(selesai, tenggat)
        if mulai >= selesai_efektif:
            continue

        waktu_sekarang = mulai

        while waktu_sekarang < selesai_efektif and sisa_estimasi > 0:
            # Durasi maksimal blok yang bisa diambil
            durasi_blok = min(
                float(maks_blok_menit),
                sisa_estimasi,
                (selesai_efektif - waktu_sekarang).total_seconds() / 60,
            )

            waktu_selesai_blok = waktu_sekarang + timedelta(minutes=durasi_blok)
            blok_jadwal.append((waktu_sekarang, waktu_selesai_blok))

            sisa_estimasi -= durasi_blok
            waktu_sekarang = waktu_selesai_blok

    return blok_jadwal