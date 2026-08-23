import pytest


# =====================================================
# Test: View Complaint Details
# =====================================================

def test_staff_view_complaint(
    client,
    staff_headers,
    assigned_complaint
):

    response = client.get(
        f"/complaints/{assigned_complaint}",
        headers=staff_headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: Update Complaint -> IN_PROGRESS
# =====================================================

def test_update_status_in_progress(
    client,
    staff_headers,
    assigned_complaint
):

    response = client.put(
        f"/staff/complaints/{assigned_complaint}/status",
        headers=staff_headers,
        json={
            "status": "IN_PROGRESS",
            "comment": "Work started."
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: Update Complaint -> RESOLVED
# =====================================================

def test_update_status_resolved(
    client,
    staff_headers,
    assigned_complaint
):

    response = client.put(
        f"/staff/complaints/{assigned_complaint}/status",
        headers=staff_headers,
        json={
            "status": "RESOLVED",
            "comment": "Issue completely resolved."
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: Invalid Status Transition
# =====================================================

def test_invalid_status_transition(
    client,
    staff_headers,
    assigned_complaint
):

    response = client.put(
        f"/staff/complaints/{assigned_complaint}/status",
        headers=staff_headers,
        json={
            "status": "RESOLVED",
            "comment": "Trying invalid transition."
        }
    )

    assert response.status_code in [400, 409]