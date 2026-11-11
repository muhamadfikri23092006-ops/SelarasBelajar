import pytest
from services.tools.capacity import check_capacity


def test_kapasitas_cukup():
    result = check_capacity(120, 90)
    assert result == {"cukup": True, "selisih": 30}


def test_kapasitas_pas():
    result = check_capacity(60, 60)
    assert result == {"cukup": True, "selisih": 0}


def test_kapasitas_kurang():
    result = check_capacity(60, 90)
    assert result == {"cukup": False, "selisih": -30}


def test_menit_negatif():
    with pytest.raises(ValueError):
        check_capacity(-10, 50)
    with pytest.raises(ValueError):
        check_capacity(50, -10)