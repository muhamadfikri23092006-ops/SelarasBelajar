from datetime import datetime

from services.tools.effort import estimate_effort
from services.tools.capacity import check_capacity
from services.tools.scheduler import hitung_menit_tersedia, schedule_blocks
from services.verifier.schedule_check import verify_schedule


def plan_task(
    *,
    jenis: str,
    bobot: float,
    slot_kosong: list[tuple[datetime, datetime]],
    tenggat: datetime,
    maks_blok_menit: int = 60,
) -> dict:
    """Merangkai estimasi, kecukupan waktu, penjadwalan, dan verifikasi.
    Kesalahan masukan (mis. jenis tidak dikenal) dibiarkan merambat sebagai
    ValueError; orkestrator yang menanganinya.
    """
    # TODO 1: hitung estimasi_menit dari jenis dan bobot
    estimasi_menit = estimate_effort(jenis=jenis, bobot=bobot)

    # TODO 2: hitung menit_tersedia dari slot_kosong dan tenggat
    menit_tersedia = hitung_menit_tersedia(
        slot_kosong=slot_kosong,
        tenggat=tenggat,
    )

    # TODO 3: kecukupan = check_capacity(...) (ingat: keyword-only!)
    kecukupan = check_capacity(
        total_estimasi_menit=estimasi_menit,
        menit_tersedia=menit_tersedia,
    )

    # TODO 4: blok = schedule_blocks(...)
    blok = schedule_blocks(
        estimasi_menit=estimasi_menit,
        slot_kosong=slot_kosong,
        tenggat=tenggat,
        maks_blok_menit=maks_blok_menit,
    )

    # TODO 5: verifikasi = verify_schedule(...)
    verifikasi = verify_schedule(
        blok=blok,
        tenggat=tenggat,
        maks_blok_menit=maks_blok_menit,
        estimasi_menit=estimasi_menit,
    )

    # TODO 6: tentukan status (urutan prioritas penting!)
    if not verifikasi["valid"]:
        status = "GAGAL_VERIFIKASI"
    elif not kecukupan["cukup"]:
        status = "WAKTU_TIDAK_CUKUP"
    else:
        status = "SELESAI"

    # TODO 7: kembalikan dict lengkap
    return {
        "status": status,
        "estimasi_menit": estimasi_menit,
        "menit_tersedia": menit_tersedia,
        "kecukupan": kecukupan,
        "blok": blok,
        "verifikasi": verifikasi,
    }