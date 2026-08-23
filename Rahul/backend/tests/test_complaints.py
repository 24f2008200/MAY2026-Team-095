"""
Complaint API Test Cases
"""


# =====================================================
# Complaint Data Helper
# =====================================================

def valid_complaint(category_id, suffix=""):
    """
    Returns valid complaint data using the dedicated
    pytest category.
    """
    return {
        "category_id": category_id,
        "title": f"Water leakage in kitchen {suffix}".strip(),
        "description": (
            "There is continuous water leakage under "
            "the kitchen sink."
        ),
        "location": "Flat A202, Kitchen",
        "priority": "MEDIUM",
    }


INVALID_CATEGORY_COMPLAINT = {
    "category_id": 999999,
    "title": "Water leakage in kitchen",
    "description": "There is continuous water leakage under the kitchen sink.",
    "location": "Flat A202, Kitchen",
    "priority": "MEDIUM",
}


# =====================================================
# CREATE COMPLAINT
# =====================================================

def test_create_complaint_success(
    client,
    resident_headers,
    category_id,
):

    complaint_data = valid_complaint(
        category_id,
        "Create Test",
    )

    response = client.post(
        "/complaints",
        json=complaint_data,
        headers=resident_headers,
    )

    assert response.status_code == 201, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert data["message"] == "Complaint created successfully."
    assert "complaint" in data

    complaint = data["complaint"]

    assert complaint["title"] == complaint_data["title"]
    assert complaint["priority"] == "MEDIUM"
    assert complaint["status"] == "OPEN"


def test_create_complaint_invalid_category(
    client,
    resident_headers,
):

    response = client.post(
        "/complaints",
        json=INVALID_CATEGORY_COMPLAINT,
        headers=resident_headers,
    )

    assert response.status_code == 400, response.get_json()

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Invalid or inactive category."


def test_create_complaint_staff_forbidden(
    client,
    staff_headers,
    category_id,
):

    response = client.post(
        "/complaints",
        json=valid_complaint(
            category_id,
            "Staff Forbidden",
        ),
        headers=staff_headers,
    )

    assert response.status_code == 403, response.get_json()


def test_create_complaint_admin_forbidden(
    client,
    admin_headers,
    category_id,
):

    response = client.post(
        "/complaints",
        json=valid_complaint(
            category_id,
            "Admin Forbidden",
        ),
        headers=admin_headers,
    )

    assert response.status_code == 403, response.get_json()


def test_create_complaint_without_token(
    client,
    category_id,
):

    response = client.post(
        "/complaints",
        json=valid_complaint(
            category_id,
            "No Token",
        ),
    )

    assert response.status_code == 401


def test_create_complaint_invalid_token(
    client,
    category_id,
):

    response = client.post(
        "/complaints",
        json=valid_complaint(
            category_id,
            "Invalid Token",
        ),
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data


# =====================================================
# LIST COMPLAINTS
# =====================================================

def test_list_complaints_resident(
    client,
    resident_headers,
):

    response = client.get(
        "/complaints",
        headers=resident_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert "complaints" in data
    assert isinstance(data["complaints"], list)
    assert "pagination" in data


def test_list_complaints_staff(
    client,
    staff_headers,
):

    response = client.get(
        "/complaints",
        headers=staff_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert "complaints" in data
    assert isinstance(data["complaints"], list)


def test_list_complaints_admin(
    client,
    admin_headers,
):

    response = client.get(
        "/complaints",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert "complaints" in data
    assert isinstance(data["complaints"], list)


def test_list_complaints_without_token(client):

    response = client.get("/complaints")

    assert response.status_code == 401


def test_list_complaints_invalid_token(client):

    response = client.get(
        "/complaints",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data


# =====================================================
# GET COMPLAINT DETAILS
# =====================================================

def test_get_complaint_success(
    client,
    resident_headers,
    resident_complaint,
):

    response = client.get(
        f"/complaints/{resident_complaint}",
        headers=resident_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert "complaint" in data
    assert data["complaint"]["id"] == resident_complaint


def test_get_complaint_invalid_id(
    client,
    resident_headers,
):

    response = client.get(
        "/complaints/999999999",
        headers=resident_headers,
    )

    assert response.status_code == 404, response.get_json()


def test_get_complaint_without_token(client):

    response = client.get("/complaints/999999999")

    assert response.status_code == 401


def test_get_complaint_invalid_token(client):

    response = client.get(
        "/complaints/999999999",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data


# =====================================================
# UPDATE COMPLAINT
# =====================================================

UPDATE_COMPLAINT = {
    "title": "Severe Water Leakage in Kitchen",
    "description": "Water leakage and sink related issues.",
    "location": "Flat A202",
    "priority": "HIGH",
}


def test_update_complaint_success(
    client,
    resident_headers,
    category_id,
):

    # Create a fresh complaint specifically for this test.
    complaint_data = valid_complaint(
        category_id,
        "Update Test",
    )

    response = client.post(
        "/complaints",
        json=complaint_data,
        headers=resident_headers,
    )

    assert response.status_code == 201, response.get_json()

    complaint_id = response.get_json()["complaint"]["id"]

    # Update the newly created complaint.
    response = client.put(
        f"/complaints/{complaint_id}",
        json=UPDATE_COMPLAINT,
        headers=resident_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True

    complaint = data["complaint"]

    assert complaint["title"] == UPDATE_COMPLAINT["title"]
    assert complaint["priority"] == "HIGH"


def test_update_complaint_invalid_id(
    client,
    resident_headers,
):

    response = client.put(
        "/complaints/999999999",
        json=UPDATE_COMPLAINT,
        headers=resident_headers,
    )

    assert response.status_code == 404, response.get_json()


def test_update_complaint_without_token(client):

    response = client.put(
        "/complaints/999999999",
        json=UPDATE_COMPLAINT,
    )

    assert response.status_code == 401


def test_update_complaint_invalid_token(client):

    response = client.put(
        "/complaints/999999999",
        json=UPDATE_COMPLAINT,
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data


# =====================================================
# COMPLAINT TIMELINE
# =====================================================

def test_get_timeline_success(
    client,
    resident_headers,
    resident_complaint,
):

    response = client.get(
        f"/complaints/{resident_complaint}/timeline",
        headers=resident_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert data["complaint_id"] == resident_complaint


def test_get_timeline_invalid_id(
    client,
    resident_headers,
):

    response = client.get(
        "/complaints/999999999/timeline",
        headers=resident_headers,
    )

    assert response.status_code == 404, response.get_json()


def test_get_timeline_without_token(client):

    response = client.get(
        "/complaints/999999999/timeline",
    )

    assert response.status_code == 401


def test_get_timeline_invalid_token(client):

    response = client.get(
        "/complaints/999999999/timeline",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data


# =====================================================
# FEEDBACK
# =====================================================

FEEDBACK = {
    "rating": 5,
    "comment": "Issue resolved quickly.",
}


def test_feedback_open_complaint(
    client,
    resident_headers,
    resident_complaint,
):

    response = client.post(
        f"/complaints/{resident_complaint}/feedback",
        json=FEEDBACK,
        headers=resident_headers,
    )

    assert response.status_code == 400, response.get_json()

    data = response.get_json()

    assert data["success"] is False
    assert (
        data["message"]
        == "Feedback can only be submitted for resolved or closed complaints."
    )


def test_feedback_without_token(client):

    response = client.post(
        "/complaints/999999999/feedback",
        json=FEEDBACK,
    )

    assert response.status_code == 401


def test_feedback_invalid_token(client):

    response = client.post(
        "/complaints/999999999/feedback",
        json=FEEDBACK,
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data


# =====================================================
# ATTACHMENTS
# =====================================================

def test_upload_attachment_without_file(
    client,
    resident_headers,
    resident_complaint,
):

    response = client.post(
        f"/complaints/{resident_complaint}/attachments",
        headers=resident_headers,
    )

    assert response.status_code == 400, response.get_json()

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "No file provided."


def test_upload_attachment_without_token(client):

    response = client.post(
        "/complaints/999999999/attachments",
    )

    assert response.status_code == 401


def test_upload_attachment_invalid_token(client):

    response = client.post(
        "/complaints/999999999/attachments",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data