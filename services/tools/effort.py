import math

MENIT_DASAR = {
    "rangkuman": 90,
    "makalah": 240,
    "laporan_praktikum": 180,
    "presentasi": 150,
    "kuis": 60,
}


def estimate_effort(jenis: str, bobot: float) -> int:
    """Menghitung estimasi waktu pengerjaan tugas dalam satuan menit.

    Rumus: ceil(menit_dasar[jenis] * (1 + bobot))
    """
    # Validasi jenis tugas
    if jenis not in MENIT_DASAR:
        raise ValueError(
            f"Jenis tugas '{jenis}' tidak dikenal. Pilih salah satu dari: {list(MENIT_DASAR.keys())}"
        )

    # Validasi rentang bobot (menolak bobot < 0.0, bobot > 1.0, dan float('nan'))
    if not (0.0 <= bobot <= 1.0):
        raise ValueError(
            f"Bobot harus berada dalam rentang 0.0 sampai 1.0 (diterima: {bobot})"
        )

    # Bulatkan nilai perkalian presisi float sebelum ceil
    estimasi_mentah = round(MENIT_DASAR[jenis] * (1.0 + bobot), 6)

    return math.ceil(estimasi_mentah)