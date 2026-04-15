"""ExternalDataConnector: offline fallback + HTTP path behavior."""
from unittest.mock import patch, MagicMock

from src.data_connectors.live_sync import ExternalDataConnector


def test_fallback_when_disabled():
    conn = ExternalDataConnector(enabled=False)
    snap = conn.sync_all()
    assert snap["traffic"]["is_real_data"] is False
    assert snap["weather"]["is_real_data"] is False
    assert "timestamp" in snap


def test_opensky_live_parse():
    conn = ExternalDataConnector(enabled=True)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"states": [["a", "b"], ["c", "d"], ["e", "f"]]}
    with patch("src.data_connectors.live_sync.requests.get", return_value=mock_resp):
        traffic = conn.fetch_opensky_traffic()
    assert traffic["is_real_data"] is True
    assert traffic["active_icao_count"] == 3
    assert traffic["source"] == "opensky"


def test_opensky_fallback_on_error():
    conn = ExternalDataConnector(enabled=True)
    with patch("src.data_connectors.live_sync.requests.get", side_effect=RuntimeError("boom")):
        traffic = conn.fetch_opensky_traffic()
    assert traffic["is_real_data"] is False
    assert traffic["source"] == "fallback"


def test_open_meteo_live_parse():
    conn = ExternalDataConnector(enabled=True)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 22.5,
            "wind_speed_10m": 8.2,
            "wind_direction_10m": 240,
            "visibility": 9000,
            "pressure_msl": 1013.1,
        }
    }
    with patch("src.data_connectors.live_sync.requests.get", return_value=mock_resp):
        weather = conn.fetch_real_metar("IST")
    assert weather["is_real_data"] is True
    assert weather["condition"] == "VFR"
    assert weather["temperature_c"] == 22.5
    assert weather["source"] == "open-meteo"


def test_weather_cache_reuse():
    conn = ExternalDataConnector(enabled=True)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"current": {"visibility": 9000, "temperature_2m": 20}}
    with patch("src.data_connectors.live_sync.requests.get", return_value=mock_resp) as mget:
        conn.fetch_real_metar("IST")
        conn.fetch_real_metar("IST")
        assert mget.call_count == 1
