import pytest


VALID_PAYLOAD = {
    "median_income_in_block": 8.3252,
    "median_house_age_in_block": 41,
    "average_rooms": 6.98,
    "average_bedrooms": 1.02,
    "population_per_block": 322,
    "average_house_occupancy": 2.56,
    "block_latitude": 37.88,
    "block_longitude": -122.23,
}


def test_prediction(test_client, auth_headers) -> None:
    response = test_client.post(
        "/api/model/predict",
        json=VALID_PAYLOAD,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "median_house_value" in data
    assert "currency" in data
    assert isinstance(data["median_house_value"], float)
    assert data["median_house_value"] > 0
    assert data["currency"] == "USD"


def test_prediction_no_payload(test_client, auth_headers) -> None:
    response = test_client.post(
        "/api/model/predict", json={}, headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "field, value",
    [
        ("median_income_in_block", -1),
        ("average_rooms", 0),
        ("average_bedrooms", -5),
        ("population_per_block", 0),
        ("average_house_occupancy", -2),
        ("block_latitude", 100),
        ("block_latitude", -100),
        ("block_longitude", 200),
        ("block_longitude", -200),
    ],
)
def test_prediction_invalid_field_values(
    test_client, auth_headers, field, value
) -> None:
    payload = {**VALID_PAYLOAD, field: value}
    response = test_client.post(
        "/api/model/predict", json=payload, headers=auth_headers
    )
    assert response.status_code == 422


def test_prediction_missing_field(test_client, auth_headers) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "average_rooms"}
    response = test_client.post(
        "/api/model/predict", json=payload, headers=auth_headers
    )
    assert response.status_code == 422
