def check_capacity(*, menit_tersedia: int, total_estimasi_menit: int) -> dict:
    """Mengecek apakah kapasitas waktu yang tersedia cukup untuk menangani total estimasi tugas.

    Memaksa pemanggilan menggunakan keyword arguments untuk mencegah kesalahan urutan parameter.

    Returns:
        dict: {'cukup': bool, 'selisih': int}
    """
    if menit_tersedia < 0:
        raise ValueError("Menit tersedia tidak boleh negatif.")

    if total_estimasi_menit < 0:
        raise ValueError("Total estimasi menit tidak boleh negatif.")

    selisih = menit_tersedia - total_estimasi_menit
    cukup = selisih >= 0

    return {"cukup": cukup, "selisih": selisih}