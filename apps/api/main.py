import os
import sqlite3
from collections.abc import Generator
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict

from services.agent.planner import plan_task
from services.storage.db import (
    create_task,
    get_profile,
    get_task,
    init_db,
    list_tasks,
    save_profile,
    update_task_status,
)

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


class DasarOut(BaseModel):
    menit_dasar: int
    bobot: float


class PlanRequest(BaseModel):
    jenis: str
    bobot: float
    slot_kosong: list[SlotIn]
    tenggat: datetime
    maks_blok_menit: int = 60


class PlanResponse(BaseModel):
    status: str
    estimasi_menit: int
    dasar: DasarOut
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
        dasar=DasarOut(**hasil["dasar"]),
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


# --- Skema Pydantic Tugas ---


class TaskIn(BaseModel):
    user_id: str
    judul: str
    matkul: str = ""
    jenis: str
    bobot: float
    tenggat: datetime


class TaskStatusUpdate(BaseModel):
    status: str


class TaskOut(BaseModel):
    id: int
    user_id: str
    judul: str
    matkul: str
    jenis: str
    bobot: float
    tenggat: str
    status: str
    status_rencana: str
    blok: list[BlokOut]


def _format_task_out(tugas: dict) -> dict:
    """Konversi objek datetime pada dict tugas menjadi teks ISO untuk respons API."""
    return {
        "id": tugas["id"],
        "user_id": tugas["user_id"],
        "judul": tugas["judul"],
        "matkul": tugas["matkul"],
        "jenis": tugas["jenis"],
        "bobot": tugas["bobot"],
        "tenggat": tugas["tenggat"].isoformat(),
        "status": tugas["status"],
        "status_rencana": tugas["status_rencana"],
        "blok": [
            {"mulai": mulai.isoformat(), "selesai": selesai.isoformat()}
            for mulai, selesai in tugas["blok"]
        ],
    }


# --- Endpoint Tugas ---


@app.post("/api/v1/tasks", response_model=TaskOut, status_code=201)
def create_task_endpoint(
    req: TaskIn,
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    if get_profile(koneksi, user_id=req.user_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profil dengan user_id '{req.user_id}' tidak ditemukan.",
        )

    try:
        tugas_id = create_task(
            koneksi,
            user_id=req.user_id,
            judul=req.judul,
            matkul=req.matkul,
            jenis=req.jenis,
            bobot=req.bobot,
            tenggat=req.tenggat,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tugas_baru = get_task(koneksi, tugas_id=tugas_id)
    if tugas_baru is None:
        raise HTTPException(
            status_code=500, detail="Tugas gagal dimuat setelah dibuat."
        )
    return _format_task_out(tugas_baru)


@app.get("/api/v1/tasks", response_model=list[TaskOut])
def list_tasks_endpoint(
    user_id: str,
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    daftar_tugas = list_tasks(koneksi, user_id=user_id)
    return [_format_task_out(t) for t in daftar_tugas]


@app.get("/api/v1/tasks/{tugas_id}", response_model=TaskOut)
def get_task_endpoint(
    tugas_id: int,
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    tugas = get_task(koneksi, tugas_id=tugas_id)
    if tugas is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tugas dengan id {tugas_id} tidak ditemukan.",
        )
    return _format_task_out(tugas)


@app.patch("/api/v1/tasks/{tugas_id}", response_model=TaskOut)
def patch_task_status_endpoint(
    tugas_id: int,
    req: TaskStatusUpdate,
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    try:
        diubah = update_task_status(
            koneksi,
            tugas_id=tugas_id,
            status=req.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not diubah:
        raise HTTPException(
            status_code=404,
            detail=f"Tugas dengan id {tugas_id} tidak ditemukan.",
        )

    tugas_terbaru = get_task(koneksi, tugas_id=tugas_id)
    if tugas_terbaru is None:
        raise HTTPException(
            status_code=500, detail="Tugas gagal dimuat setelah diperbarui."
        )
    return _format_task_out(tugas_terbaru)