import os
import sqlite3
from collections.abc import Generator
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict

from services.agent.planner import plan_task
from services.storage.db import get_profile, init_db, save_profile

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

def get_koneksi() -> Generator[sqlite3.Connection, None, None]:
    db_path = os.getenv("SELARAS_DB", "selaras.db")
    koneksi = init_db(db_path)
    try:
        yield koneksi
    finally:
        koneksi.close()

# --- Skema Pydantic Profil VARK ---


class SkorVARK(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visual: int
    aural: int
    read_write: int
    kinestetik: int


class ProfileRequest(BaseModel):
    nama: str
    skor: SkorVARK


class ProfileResponse(BaseModel):
    user_id: str
    nama: str
    skor: SkorVARK
    dibuat_pada: str

# --- Endpoint Profil ---


@app.put("/api/v1/profile/{user_id}", response_model=ProfileResponse)
def upsert_profile_endpoint(
    user_id: str,
    req: ProfileRequest,
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    try:
        save_profile(
            koneksi,
            user_id=user_id,
            nama=req.nama,
            skor=req.skor.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    profil = get_profile(koneksi, user_id=user_id)
    if profil is None:
        raise HTTPException(
            status_code=500, detail="Profil gagal dimuat setelah disimpan."
        )
    return profil


@app.get("/api/v1/profile/{user_id}", response_model=ProfileResponse)
def read_profile_endpoint(
    user_id: str,
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    profil = get_profile(koneksi, user_id=user_id)
    if profil is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profil dengan user_id '{user_id}' tidak ditemukan.",
        )
    return profil