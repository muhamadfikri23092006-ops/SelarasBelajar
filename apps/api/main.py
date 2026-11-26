import os
import sqlite3
from collections.abc import Generator
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from services.agent.planner import plan_task
from services.storage.db import (
    create_task,
    get_profile,
    get_task,
    get_user_by_token,
    init_db,
    issue_token,
    list_tasks,
    save_blocks,
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


class TaskPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_kosong: list[SlotIn]
    maks_blok_menit: int = 60


class PlanResponse(BaseModel):
    status: str
    estimasi_menit: int
    dasar: DasarOut
    menit_tersedia: int
    kecukupan: dict[str, Any]
    blok: list[BlokOut]
    verifikasi: VerifikasiOut


def _jalankan_rencana(
    *,
    jenis: str,
    bobot: float,
    slot_kosong: list[SlotIn],
    tenggat: datetime,
    maks_blok_menit: int,
) -> dict[str, Any]:
    """Menjalankan plan_task dan memetakan ValueError menjadi HTTPException 422."""
    slot_tuples = [(slot.mulai, slot.selesai) for slot in slot_kosong]
    try:
        return plan_task(
            jenis=jenis,
            bobot=bobot,
            slot_kosong=slot_tuples,
            tenggat=tenggat,
            maks_blok_menit=maks_blok_menit,
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err


def _format_plan_response(hasil: dict[str, Any]) -> PlanResponse:
    """Mengonversi dict hasil plan_task menjadi model PlanResponse."""
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


@app.post("/api/v1/plan", response_model=PlanResponse)
def buat_rencana(req: PlanRequest) -> PlanResponse:
    hasil = _jalankan_rencana(
        jenis=req.jenis,
        bobot=req.bobot,
        slot_kosong=req.slot_kosong,
        tenggat=req.tenggat,
        maks_blok_menit=req.maks_blok_menit,
    )
    return _format_plan_response(hasil)


def get_koneksi() -> Generator[sqlite3.Connection, None, None]:
    db_path = os.getenv("SELARAS_DB", "selaras.db")
    koneksi = init_db(db_path)
    try:
        yield koneksi
    finally:
        koneksi.close()


def get_user_saat_ini(
    authorization: str | None = Header(default=None),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
) -> str:
    """Memvalidasi header Authorization: Bearer <token> dan mengembalikan user_id."""
    unauthorized = HTTPException(
        status_code=401,
        detail="Token autentikasi tidak valid atau tidak ditemukan.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization:
        raise unauthorized

    skema, sep, token = authorization.partition(" ")
    if skema != "Bearer" or not sep or not token.strip() or " " in token.strip():
        raise unauthorized

    user_id = get_user_by_token(koneksi, token=token.strip())
    if user_id is None:
        raise unauthorized

    return user_id


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


class ProfileCreatedResponse(ProfileResponse):
    token: str


# --- Endpoint Profil ---


@app.put(
    "/api/v1/profile/{user_id}",
    response_model=ProfileCreatedResponse | ProfileResponse,
)
def upsert_profile_endpoint(
    user_id: str,
    req: ProfileRequest,
    response: Response,
    authorization: str | None = Header(default=None),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    profil_lama = get_profile(koneksi, user_id=user_id)

    if profil_lama is None:
        # Pendaftaran terbuka -> 201 dengan token baru
        try:
            save_profile(
                koneksi,
                user_id=user_id,
                nama=req.nama,
                skor=req.skor.model_dump(),
            )
            token_baru = issue_token(koneksi, user_id=user_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        profil = get_profile(koneksi, user_id=user_id)
        if profil is None:
            raise HTTPException(
                status_code=500, detail="Profil gagal dimuat setelah disimpan."
            )
        response.status_code = 201
        return {**profil, "token": token_baru}

    # Profil sudah ada -> wajib autentikasi dan pemilik harus cocok
    user_terautentikasi = get_user_saat_ini(
        authorization=authorization,
        koneksi=koneksi,
    )
    if user_terautentikasi != user_id:
        raise HTTPException(
            status_code=403,
            detail="Tidak diizinkan mengubah profil pengguna lain.",
        )

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
    response.status_code = 200
    return profil


@app.get("/api/v1/profile/{user_id}", response_model=ProfileResponse)
def read_profile_endpoint(
    user_id: str,
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    if user_terautentikasi != user_id:
        raise HTTPException(
            status_code=403,
            detail="Tidak diizinkan mengakses profil pengguna lain.",
        )

    profil = get_profile(koneksi, user_id=user_id)
    if profil is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profil dengan user_id '{user_id}' tidak ditemukan.",
        )
    return profil


# --- Skema Pydantic Tugas ---


class TaskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    try:
        tugas_id = create_task(
            koneksi,
            user_id=user_terautentikasi,
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
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    daftar_tugas = list_tasks(koneksi, user_id=user_terautentikasi)
    return [_format_task_out(t) for t in daftar_tugas]


@app.get("/api/v1/tasks/{tugas_id}", response_model=TaskOut)
def get_task_endpoint(
    tugas_id: int,
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    tugas = get_task(koneksi, tugas_id=tugas_id)
    if tugas is None or tugas["user_id"] != user_terautentikasi:
        raise HTTPException(
            status_code=404,
            detail=f"Tugas dengan id {tugas_id} tidak ditemukan.",
        )
    return _format_task_out(tugas)


@app.patch("/api/v1/tasks/{tugas_id}", response_model=TaskOut)
def patch_task_status_endpoint(
    tugas_id: int,
    req: TaskStatusUpdate,
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    tugas = get_task(koneksi, tugas_id=tugas_id)
    if tugas is None or tugas["user_id"] != user_terautentikasi:
        raise HTTPException(
            status_code=404,
            detail=f"Tugas dengan id {tugas_id} tidak ditemukan.",
        )

    try:
        update_task_status(
            koneksi,
            tugas_id=tugas_id,
            status=req.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tugas_terbaru = get_task(koneksi, tugas_id=tugas_id)
    if tugas_terbaru is None:
        raise HTTPException(
            status_code=500, detail="Tugas gagal dimuat setelah diperbarui."
        )
    return _format_task_out(tugas_terbaru)


@app.post("/api/v1/tasks/{tugas_id}/plan/preview", response_model=PlanResponse)
def preview_task_plan_endpoint(
    tugas_id: int,
    req: TaskPlanRequest,
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    tugas = get_task(koneksi, tugas_id=tugas_id)
    if tugas is None or tugas["user_id"] != user_terautentikasi:
        raise HTTPException(
            status_code=404,
            detail=f"Tugas dengan id {tugas_id} tidak ditemukan.",
        )

    hasil = _jalankan_rencana(
        jenis=tugas["jenis"],
        bobot=tugas["bobot"],
        slot_kosong=req.slot_kosong,
        tenggat=tugas["tenggat"],
        maks_blok_menit=req.maks_blok_menit,
    )
    return _format_plan_response(hasil)


@app.post("/api/v1/tasks/{tugas_id}/plan/confirm", response_model=TaskOut)
def confirm_task_plan_endpoint(
    tugas_id: int,
    req: TaskPlanRequest,
    user_terautentikasi: str = Depends(get_user_saat_ini),
    koneksi: sqlite3.Connection = Depends(get_koneksi),
):
    tugas = get_task(koneksi, tugas_id=tugas_id)
    if tugas is None or tugas["user_id"] != user_terautentikasi:
        raise HTTPException(
            status_code=404,
            detail=f"Tugas dengan id {tugas_id} tidak ditemukan.",
        )

    if tugas["status"] == "SELESAI":
        raise HTTPException(
            status_code=409,
            detail="Tugas yang sudah SELESAI tidak dapat dijadwalkan ulang.",
        )

    hasil = _jalankan_rencana(
        jenis=tugas["jenis"],
        bobot=tugas["bobot"],
        slot_kosong=req.slot_kosong,
        tenggat=tugas["tenggat"],
        maks_blok_menit=req.maks_blok_menit,
    )

    if hasil["status"] != "TERJADWAL":
        raise HTTPException(
            status_code=409,
            detail=f"Penjadwalan gagal dengan status '{hasil['status']}'.",
        )

    try:
        save_blocks(
            koneksi,
            tugas_id=tugas_id,
            blok=hasil["blok"],
            status_rencana="TERJADWAL",
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err

    tugas_terbaru = get_task(koneksi, tugas_id=tugas_id)
    if tugas_terbaru is None:
        raise HTTPException(
            status_code=500, detail="Tugas gagal dimuat setelah penjadwalan."
        )
    return _format_task_out(tugas_terbaru)