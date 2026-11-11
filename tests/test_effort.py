import math
import pytest
from services.tools.effort import estimate_effort


def test_rangkuman_bobot_kecil():
    assert estimate_effort("rangkuman", 0.1) == 99


def test_makalah_bobot_sedang():
    assert estimate_effort("makalah", 0.5) == 360


def test_makalah_bobot_maksimal():
    assert estimate_effort("makalah", 1.0) == 480


def test_laporan_praktikum_dan_presentasi():
    assert estimate_effort("laporan_praktikum", 0.2) == 216
    assert estimate_effort("presentasi", 0.5) == 225


def test_kuis_tanpa_bobot():
    assert estimate_effort("kuis", 0.0) == 60


def test_pembulatan_ke_atas():
    assert estimate_effort("rangkuman", 0.15) == 104


def test_jenis_tidak_dikenal():
    with pytest.raises(ValueError):
        estimate_effort("tidak_ada", 0.5)


def test_bobot_di_luar_rentang_dan_nan():
    with pytest.raises(ValueError):
        estimate_effort("kuis", 1.5)

    with pytest.raises(ValueError):
        estimate_effort("kuis", -0.1)

    # float("nan") langsung dipanggil dari fungsi bawaan float(), tanpa perlu di-import
    with pytest.raises(ValueError):
        estimate_effort("kuis", float("nan"))