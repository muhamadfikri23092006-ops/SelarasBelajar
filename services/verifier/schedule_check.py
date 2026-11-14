from datetime import datetime


def _tambah_pelanggaran(daftar: list[str], kode: str) -> None:
    if kode not in daftar:
        daftar.append(kode)


def verify_schedule(
    *,
    blok: list[tuple[datetime, datetime]],
    tenggat: datetime,
    maks_blok_menit: int,
    estimasi_menit: int,
) -> dict[str, bool | list[str]]:
    """
    Memvalidasi daftar blok jadwal terhadap aturan keras RB-05.
    Mengembalikan status validitas dan daftar kode pelanggaran unik.
    """
    pelanggaran: list[str] = []
    total_durasi_menit = 0.0

    # 1. Cek tiap blok: tidak valid? lewat tenggat? terlalu panjang?
    for mulai, selesai in blok:
        durasi_menit = (selesai - mulai).total_seconds() / 60.0

        if mulai >= selesai:
            _tambah_pelanggaran(pelanggaran, "BLOK_TIDAK_VALID")
        else:
            total_durasi_menit += durasi_menit
            if durasi_menit > maks_blok_menit:
                _tambah_pelanggaran(pelanggaran, "BLOK_TERLALU_PANJANG")

        if selesai > tenggat:
            _tambah_pelanggaran(pelanggaran, "MELEWATI_TENGGAT")

    # 2. Urutkan salinan blok berdasarkan waktu mulai, lalu cek pasangan berurutan
    blok_terurut = sorted(blok, key=lambda b: b[0])
    for i in range(len(blok_terurut) - 1):
        blok_saat_ini = blok_terurut[i]
        blok_berikutnya = blok_terurut[i + 1]

        if blok_berikutnya[0] < blok_saat_ini[1]:
            _tambah_pelanggaran(pelanggaran, "TUMPANG_TINDIH")

    # 3. Hitung total durasi dan bandingkan dengan estimasi
    if total_durasi_menit > estimasi_menit:
        _tambah_pelanggaran(pelanggaran, "TOTAL_MELEBIHI_ESTIMASI")

    return {
        "valid": len(pelanggaran) == 0,
        "pelanggaran": pelanggaran,
    }