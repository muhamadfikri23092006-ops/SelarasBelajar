import pytest
from services.tools.effort import estimate_effort


def test_rangkuman_bobot_kecil():
    assert estimate_effort("rangkuman", 0.1) == 99


def test_makalah_bobot_sedang():
    assert estimate_effort("makalah", 0.5) == 360


def test_kuis_tanpa_bobot():
    assert estimate_effort("kuis", 0.0) == 60


def test_jenis_tidak_dikenal():
    with pytest.raises(ValueError):
        estimate_effort("tidak_ada", 0.5)


def test_bobot_di_luar_rentang():
    with pytest.raises(ValueError):
        estimate_effort("kuis", 1.5)
    with pytest.raises(ValueError):
        estimate_effort("kuis", -0.1)