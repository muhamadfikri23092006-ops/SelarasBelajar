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