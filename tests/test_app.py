from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# def test_get_users():
#     response = client.get("/users")

#     assert response.status_code == 200
#     assert len(response.json()) >= 2


# def test_get_user():
#     response = client.get("/users/1")

#     assert response.status_code == 200
#     assert response.json()["name"] == "Kim"


def test_user_not_found():
    response = client.get("/users/999")

    assert response.status_code == 404