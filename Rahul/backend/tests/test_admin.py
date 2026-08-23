import random
import uuid


# =====================================================
# Test: Admin Dashboard
# =====================================================

def test_admin_dashboard(client, admin_headers):

    response = client.get(
        "/admin/dashboard",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: View Staff List
# =====================================================

def test_get_staff(client, admin_headers):

    response = client.get(
        "/admin/staff",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True


# =====================================================
# Test: Create Category
# =====================================================

def test_create_category(client, admin_headers):

    category_name = f"Pytest Category {uuid.uuid4().hex[:8]}"

    response = client.post(
        "/admin/categories",
        headers=admin_headers,
        json={
            "name": category_name,
            "description": "Category created automatically by pytest.",
        },
    )

    assert response.status_code == 201, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert data["category"]["name"] == category_name


# =====================================================
# Test: Create Staff
# =====================================================

def test_create_staff(client, admin_headers):

    unique_id = uuid.uuid4().hex[:10]

    email = f"pyteststaff_{unique_id}@example.com"

    # Generate a unique 10-digit mobile number starting with 9.
    mobile = "9" + "".join(
        str(random.randint(0, 9))
        for _ in range(9)
    )

    response = client.post(
        "/admin/staff",
        headers=admin_headers,
        json={
            "name": f"Pytest Staff {unique_id}",
            "email": email,
            "mobile_number": mobile,
            "flat_number": "S-101",
            "building": "Service Block",
            "password": "Staff@123",
            "trade": "Electrician",
        },
    )

    assert response.status_code == 201, response.get_json()

    data = response.get_json()

    assert data["success"] is True
    assert data["staff"]["email"] == email
    assert data["staff"]["mobile_number"] == mobile
    assert data["staff"]["trade"] == "Electrician"


# =====================================================
# Test: Assign Staff to Complaint
# =====================================================

def test_assign_staff(
    client,
    admin_headers,
    resident_complaint,
    staff_user_id,
):

    response = client.put(
        f"/admin/complaints/{resident_complaint}/assign",
        headers=admin_headers,
        json={
            "staff_id": staff_user_id,
        },
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()

    assert data["success"] is True