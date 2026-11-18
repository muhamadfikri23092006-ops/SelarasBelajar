from datetime import datetime
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.agent.planner import plan_task


app = FastAPI(title="SelarasBelajar API")


class SlotIn(BaseModel):
    mulai: datetime
    selesai: datetime


class BlokOut(BaseModel):
    mulai: str
    selesai: str


class VerifikasiOut(BaseModel):
    valid: bool
    pelanggaran: list[str]


class PlanRequest(BaseModel):
    jenis: str
    bobot: float
    slot_kosong: list[SlotIn]
    tenggat: datetime
    maks_blok_menit: int = 60


class PlanResponse(BaseModel):
    status: str
    estimasi_menit: int
    menit_tersedia: int
    kecukupan: dict[str, Any]
    blok: list[BlokOut]
    verifikasi: VerifikasiOut


@app.post("/api/v1/plan", response_model=PlanResponse)
def buat_rencana(req: PlanRequest) -> PlanResponse:
    # 1. Konversi SlotIn (model/dict) menjadi list tuple (datetime, datetime)
    slot_tuples = [(slot.mulai, slot.selesai) for slot in req.slot_kosong]

    # 2. Panggil logika inti plan_task; tangkap ValueError menjadi HTTP 422
    try:
        hasil = plan_task(
            jenis=req.jenis,
            bobot=req.bobot,
            slot_kosong=slot_tuples,
            tenggat=req.tenggat,
            maks_blok_menit=req.maks_blok_menit,
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err

    # 3. Konversi blok tuple menjadi list BlokOut / dict ISO string
    blok_keluaran = [
        BlokOut(mulai=mulai.isoformat(), selesai=selesai.isoformat())
        for mulai, selesai in hasil["blok"]
    ]

    return PlanResponse(
        status=hasil["status"],
        estimasi_menit=hasil["estimasi_menit"],
        menit_tersedia=hasil["menit_tersedia"],
        kecukupan=hasil["kecukupan"],
        blok=blok_keluaran,
        verifikasi=VerifikasiOut(**hasil["verifikasi"]),
    )