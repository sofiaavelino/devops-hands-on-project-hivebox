import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from main_app.main import compute_average_temperature, app
import main_app.main as main_module

def test_average_temperature():
    now = datetime.now(timezone.utc)

    boxes = [
        {
            "sensors": [
                {
                    "type": "temperature",
                    "lastMeasurement": {
                        "value": "20.0",
                        "createdAt": (now - timedelta(minutes=30)).isoformat()
                    }
                },
                {
                    "type": "temperature",
                    "lastMeasurement": {
                        "value": "22.0",
                        "createdAt": (now - timedelta(minutes=10)).isoformat()
                    }
                }
            ]
        }
    ]

    avg, count = compute_average_temperature(boxes)

    assert avg == 21.0
    assert count == 2

def test_old_data_is_ignored():
    now = datetime.now(timezone.utc)

    boxes = [
        {
            "sensors": [
                {
                    "type": "temperature",
                    "lastMeasurement": {
                        "value": "10",
                        "createdAt": (now - timedelta(hours=2)).isoformat()
                    }
                }
            ]
        }
    ]

    result = compute_average_temperature(boxes)
    assert result is None


client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_fetch_boxes():
    async def mock_fetch_boxes():
        now = datetime.now(timezone.utc)
        return [
            {
                "sensors": [
                    {
                        "type": "temperature",
                        "lastMeasurement": {
                            "value": "25",
                            "createdAt": now.isoformat()
                        }
                    }
                ]
            }
        ]

    # Patch with async lambda — TestClient will await it
    main_module.fetch_boxes = mock_fetch_boxes

def test_temperature_endpoint():
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json()["average_temperature"] == 25.0

