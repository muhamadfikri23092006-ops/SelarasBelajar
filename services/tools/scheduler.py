from datetime import datetime, timedelta


def _merge_overlapping_slots(
    slot_kosong: list[tuple[datetime, datetime]]
) -> list[tuple[datetime, datetime]]:
    """Menggabungkan slot waktu yang saling tumpang tindih atau bersambungan."""
    if not slot_kosong:
        return []

    # Urutkan slot berdasarkan waktu mulai
    slot_terurut = sorted(slot_kosong, key=lambda x: x[0])
    merged = [slot_terurut[0]]

    for current_start, current_end in slot_terurut[1:]:
        prev_start, prev_end = merged[-1]

        if current_start <= prev_end:
            # Tumpang tindih atau bersambungan, perbarui waktu selesai akhir
            merged[-1] = (prev_start, max(prev_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged


def susun_jadwal(
    estimasi_menit: int,
    slot_kosong: list[tuple[datetime, datetime]],
    tenggat: datetime,
    maks_blok_menit: int = 60,
) -> list[tuple[datetime, datetime]]:
    """Menyusun alokasi blok waktu kerja berdasarkan slot kosong dan tenggat."""
    # Validasi input
    if estimasi_menit < 0:
        raise ValueError("Estimasi menit tidak boleh negatif.")

    if maks_blok_menit <= 0:
        raise ValueError("Maksimal blok menit harus lebih besar dari 0.")

    if estimasi_menit == 0 or not slot_kosong:
        return []

    # Merging slot tumpang tindih
    slot_efektif = _merge_overlapping_slots(slot_kosong)

    sisa_estimasi = float(estimasi_menit)
    blok_jadwal = []

    for mulai, selesai in slot_efektif:
        if sisa_estimasi <= 0:
            break

        # Potong slot di tenggat
        selesai_efektif = min(selesai, tenggat)
        if mulai >= selesai_efektif:
            continue

        waktu_sekarang = mulai

        while waktu_sekarang < selesai_efektif and sisa_estimasi > 0:
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