import pytest
from rec import config
from rec.manifest import (season_to_year_quarter, build_file_name,build_df_name)

def test_season_to_year_quarter():
    assert season_to_year_quarter("106S1") == ("106", 1)
    assert season_to_year_quarter("104S3") == ("104", 3)

    with pytest.raises(ValueError) as exc_info:
        season_to_year_quarter("1061")
    assert "Invalid season: 1061" in str(exc_info.value)
    with pytest.raises(ValueError) as exc_info:
        season_to_year_quarter("")
    assert "Invalid season: " in str(exc_info.value)

def test_build_file_name():
    assert build_file_name("A", "B") == "A_lvr_land_B"
    assert build_file_name("X", "Z") == "X_lvr_land_Z"

    with pytest.raises(TypeError) as exc_info:
        build_file_name(123, "B")
    assert "city must be a str, got int" in str(exc_info.value)
    with pytest.raises(TypeError) as exc_info:
        build_file_name("Taipei", None)
    assert "trade_type must be a str, got NoneType" in str(exc_info.value)

def test_build_df_name():
    assert build_df_name("123", "7", "C", "W") == "123_7_C_W"

    with pytest.raises(TypeError) as exc_info:
        build_df_name(123, "7", "C", "W") 
    assert "year must be a str, got int" in str(exc_info.value)
    
    with pytest.raises(TypeError) as exc_info:
        build_df_name("123", 1, "C", "W")  
    assert "quarter must be a str, got int" in str(exc_info.value)
    
    with pytest.raises(TypeError) as exc_info:
        build_df_name("123", "7", None, "W")  
    assert "city must be a str, got NoneType" in str(exc_info.value)
    
    with pytest.raises(TypeError) as exc_info:
        build_df_name("123", "7", "C", [])  
    assert "trade_type must be a str, got list" in str(exc_info.value)