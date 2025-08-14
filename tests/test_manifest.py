import pytest
from rec import config
from rec.manifest import (season_to_year_quarter)

def test_season_to_year_quarter():
    assert season_to_year_quarter("106S1") == ("106", 1)
    assert season_to_year_quarter("104S3") == ("104", 3)

    with pytest.raises(ValueError) as exc_info:
        season_to_year_quarter("1061")
    assert "Invalid season: 1061" in str(exc_info.value)