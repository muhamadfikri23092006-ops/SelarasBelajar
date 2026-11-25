import pytest
from fastapi.testclient import TestClient

from apps.api.main import app, get_koneksi
from services.storage.db import init_db


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test_selaras.db"

    def override_get_koneksi():
        koneksi = init_db(db_path)
        try:
            yield koneksi
        finally:
            koneksi.close()

    app.dependency_overrides[get_koneksi] = override_get_koneksi
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def buat_profil_dengan_token(
    client: TestClient,
    user_id: str = "u01",
    nama: str = "Fikri",
    skor: dict[str, int] | None = None,
) -> dict[str, str]:
    """Membuat profil baru via PUT dan mengembalikan header Authorization Bearer."""
    if skor is None:
        skor = {"visual": 8, "aural": 5, "read_write": 7, "kinestetik": 4}

    resp = client.put(
        f"/api/v1/profile/{user_id}",
        json={"nama": nama, "skor": skor},
    )
    assert resp.status_code == 201
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}