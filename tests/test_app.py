import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Book Club": {
            "description": "Discuss books",
            "schedule": "Mondays at 3:00 PM",
            "max_participants": 3,
            "participants": ["reader@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected = {
        "Book Club": {
            "description": "Discuss books",
            "schedule": "Mondays at 3:00 PM",
            "max_participants": 3,
            "participants": ["reader@example.com"],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_adds_participant(client):
    # Arrange
    email = "new-reader@example.com"

    # Act
    response = client.post(
        "/activities/Book%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Book Club"}
    assert client.get("/activities").json()["Book Club"]["participants"] == [
        "reader@example.com",
        email,
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "new-reader@example.com"

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "reader@example.com"

    # Act
    response = client.post(
        "/activities/Book%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json()["Book Club"]["participants"] == [email]


def test_unregister_removes_all_matching_participants(client, monkeypatch):
    # Arrange
    participants = [
        "reader@example.com",
        "keep@example.com",
        "reader@example.com",
    ]
    app_module.activities["Book Club"]["participants"] = participants
    email = "reader@example.com"

    # Act
    response = client.delete(
        "/activities/Book%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Book Club"}
    assert client.get("/activities").json()["Book Club"]["participants"] == [
        "keep@example.com"
    ]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "reader@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_participant(client):
    # Arrange
    email = "not-registered@example.com"

    # Act
    response = client.delete(
        "/activities/Book%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert client.get("/activities").json()["Book Club"]["participants"] == [
        "reader@example.com"
    ]