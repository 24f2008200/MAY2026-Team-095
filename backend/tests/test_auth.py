"""
Authentication API Test Cases

Tests Included:
1. Successful Login
2. Login with Invalid Password
3. Login with Invalid Email
4. Access Profile with Valid JWT
5. Access Profile without JWT
6. Access Profile with Invalid JWT
"""


# =====================================================
# Test Login - Success
# =====================================================

def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "pytest_admin@example.com",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["message"] == "Login successful."
    assert "access_token" in data

    assert data["user"]["email"] == "pytest_admin@example.com"
    assert data["user"]["role"] == "ADMIN"


# =====================================================
# Test Login - Invalid Password
# =====================================================

def test_login_invalid_password(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "pytest_admin@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Invalid email or password."


# =====================================================
# Test Login - Invalid Email
# =====================================================

def test_login_invalid_email(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "admin123"
        }
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Invalid email or password."


# =====================================================
# Test Profile - Success
# =====================================================

def test_profile_success(client, admin_headers):
    response = client.get(
        "/auth/profile",
        headers=admin_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["user"]["email"] == "pytest_admin@example.com"
    assert data["user"]["role"] == "ADMIN"

    # Verify that important user information is returned
    assert "id" in data["user"]
    assert "name" in data["user"]
    assert "mobile_number" in data["user"]
    assert "flat_number" in data["user"]
    assert "building" in data["user"]
    assert "is_active" in data["user"]


# =====================================================
# Test Profile - Missing JWT
# =====================================================

def test_profile_without_token(client):
    response = client.get(
        "/auth/profile"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert "msg" in data


# =====================================================
# Test Profile - Invalid JWT
# =====================================================

def test_profile_invalid_token(client):
    response = client.get(
        "/auth/profile",
        headers={
            "Authorization": "Bearer invalid.jwt.token"
        }
    )

    assert response.status_code == 422

    data = response.get_json()

    assert "msg" in data