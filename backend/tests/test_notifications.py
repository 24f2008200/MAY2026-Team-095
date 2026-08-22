import pytest


# =====================================================
# Test: Get Notifications
# =====================================================

def test_get_notifications(
    client,
    resident_headers,
):

    response = client.get(
        "/notifications",
        headers=resident_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert "notifications" in data
    assert isinstance(data["notifications"], list)


# =====================================================
# Test: Mark One Notification as Read
# =====================================================

def test_mark_notification_read(
    client,
    resident_headers,
):

    # Get notifications
    response = client.get(
        "/notifications",
        headers=resident_headers,
    )

    assert response.status_code == 200

    notifications = response.get_json()["notifications"]

    if len(notifications) == 0:
        pytest.skip("No notifications available.")

    notification_id = notifications[0]["id"]

    response = client.put(
        f"/notifications/{notification_id}/read",
        headers=resident_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: Mark All Notifications as Read
# =====================================================

def test_mark_all_notifications_read(
    client,
    resident_headers,
):

    response = client.put(
        "/notifications/read-all",
        headers=resident_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: Notifications Without Token
# =====================================================

def test_notifications_without_token(client):

    response = client.get("/notifications")

    assert response.status_code == 401


# =====================================================
# Test: Notifications With Invalid Token
# =====================================================

def test_notifications_invalid_token(client):

    response = client.get(
        "/notifications",
        headers={
            "Authorization": "Bearer invalidtoken"
        },
    )

    assert response.status_code == 422