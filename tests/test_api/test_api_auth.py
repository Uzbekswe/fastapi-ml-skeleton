from fastapi_skeleton.core import messages


def test_auth_no_apikey_header(test_client) -> None:
    response = test_client.post("/api/model/predict")
    assert response.status_code == 400
    assert response.json() == {"detail": messages.NO_API_KEY}


def test_auth_wrong_apikey_header(test_client) -> None:
    response = test_client.post(
        "/api/model/predict",
        json={
            "median_income_in_block": 8.3252,
            "median_house_age_in_block": 41,
            "average_rooms": 6.98,
            "average_bedrooms": 1.02,
            "population_per_block": 322,
            "average_house_occupancy": 2.56,
            "block_latitude": 37.88,
            "block_longitude": -122.23,
        },
        headers={"X-API-Key": "WRONG_TOKEN"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": messages.AUTH_REQ}
