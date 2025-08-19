import pytest
import re
from rec import config
from rec.manifest import (season_to_year_quarter, build_file_name,build_df_name,generate_tasks)

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
    assert build_df_name("123", 7, "C", "W") == "123_7_C_W"

    with pytest.raises(TypeError) as exc_info:
        build_df_name(123, 7, "C", "W") 
    assert "year must be a str, got int" in str(exc_info.value)
    
    with pytest.raises(TypeError) as exc_info:
        build_df_name("123", "1", "C", "W")  
    assert "quarter must be a int, got str" in str(exc_info.value)
    
    with pytest.raises(TypeError) as exc_info:
        build_df_name("123", 7, None, "W")  
    assert "city must be a str, got NoneType" in str(exc_info.value)
    
    with pytest.raises(TypeError) as exc_info:
        build_df_name("123", 7, "C", [])  
    assert "trade_type must be a str, got list" in str(exc_info.value)

def test_generate_tasks_minimal_sample():
    tasks = generate_tasks(seasons=["106S1"])

    assert len(tasks) == 5
    t = next(x for x in tasks if x["season"] == "106S1" and x["city_name"] == "新北市" and x["trade_type_name"]== "不動產買賣")
    
    assert t["city_code"] == "F"
    assert t["trade_code"] == "A"
    assert t["file_name"] == "F_lvr_land_A"
    assert t["df_name"] == "106_1_F_A"

def test_generate_tasks_multiple_seasons_count():
    tasks = generate_tasks(seasons=["103S1", "103S2"])

    assert len(tasks) == 10

def test_generate_tasks_invalid_city_raises_value_error():
    # pytest.raises 的 match 是 regex，不是單純字串比對
    # [] 在 regex 中代表「字元集合」，所以 ['火星市'] 會被誤解
    # 解法：用 re.escape(...) 或改成只比對部分文字
    with pytest.raises(ValueError, match = re.escape("No valid cities found for trade type: ['火星市']")):
        generate_tasks(
            seasons=["106S1"],
            include_trade_types=["不動產買賣"],
            include_cities=["火星市"]  
        )

def test_generate_tasks_invalid_trade_types_raises_value_error():
    with pytest.raises(ValueError, match = "Invalid trade type"):
         generate_tasks(
            seasons=["106S1"],
            include_trade_types=["買賣"],
            include_cities=["台北市"]  
        )
