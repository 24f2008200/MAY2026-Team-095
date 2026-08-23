"""
Category API Test Cases

Tests Included:
1. Get categories with Resident JWT
2. Get categories with Admin JWT
3. Get categories with Staff JWT
4. Get categories without JWT
5. Get categories with Invalid JWT
"""


# =====================================================
# Resident can view categories
# =====================================================

def test_get_categories_resident(client, resident_headers):
    response = client.get(
        "/categories",
        headers=resident_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert "categories" in data
    assert isinstance(data["categories"], list)


# =====================================================
# Admin can view categories
# =====================================================

def test_get_categories_admin(client, admin_headers):
    response = client.get(
        "/categories",
        headers=admin_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert "categories" in data
    assert isinstance(data["categories"], list)


# =====================================================
# Staff can view categories
# =====================================================

def test_get_categories_staff(client, staff_headers):
    response = client.get(
        "/categories",
        headers=staff_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert "categories" in data
    assert isinstance(data["categories"], list)


# =====================================================
# Missing JWT
# =====================================================

def test_get_categories_without_token(client):
    response = client.get("/categories")

    assert response.status_code == 401


# =====================================================
# Invalid JWT
# =====================================================

def test_get_categories_invalid_token(client):
    response = client.get(
        "/categories",
        headers={
            "Authorization": "Bearer invalid.jwt.token"
        }
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data