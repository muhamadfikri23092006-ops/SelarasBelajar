import pytest
from services.tools.capacity import check_capacity


def test_kapasitas_cukup():
    result = check_capacity(menit_tersedia=120, total_estimasi_menit=90)
    assert result == {"cukup": True, "selisih": 30}


def test_kapasitas_pas():
    result = check_capacity(menit_tersedia=60, total_estimasi_menit=60)
    assert result == {"cukup": True, "selisih": 0}


def test_kapasitas_kurang():
    result = check_capacity(menit_tersedia=60, total_estimasi_menit=90)
    assert result == {"cukup": False, "selisih": -30}


def test_estimasi_nol_dengan_waktu_tersedia():
    result = check_capacity(menit_tersedia=60, total_estimasi_menit=0)
    assert result == {"cukup": True, "selisih": 60}


def test_estimasi_nol_dan_waktu_nol():
    result = check_capacity(menit_tersedia=0, total_estimasi_menit=0)
    assert result == {"cukup": True, "selisih": 0}


def test_menit_tersedia_negatif():
    with pytest.raises(ValueError):
        check_capacity(menit_tersedia=-10, total_estimasi_menit=50)


def test_estimasi_menit_negatif():
    with pytest.raises(ValueError):
        check_capacity(menit_tersedia=50, total_estimasi_menit=-10)


def test_menolak_positional_arguments():
    with pytest.raises(TypeError):
        # Memastikan pemanggilan tanpa keyword (positional) langsung error
        check_capacity(120, 90)