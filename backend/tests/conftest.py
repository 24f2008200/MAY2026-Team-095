import pytest

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole


# =====================================================
# Dedicated Test Users
# =====================================================

TEST_USERS = {
    "admin": {
        "name": "Pytest Admin",
        "email": "pytest_admin@example.com",
        "password": "admin123",
        "mobile_number": "9000000001",
        "flat_number": "ADMIN",
        "building": "Administration",
        "role": UserRole.ADMIN,
        "is_active": True,
    },

    "resident": {
        "name": "Pytest Resident",
        "email": "pytest_resident@example.com",
        "password": "resident123",
        "mobile_number": "9000000002",
        "flat_number": "A202",
        "building": "A",
        "role": UserRole.RESIDENT,
        "is_active": True,
    },

    "staff": {
        "name": "Pytest Electrician",
        "email": "pytest_staff@example.com",
        "password": "staff123",
        "mobile_number": "9000000003",
        "flat_number": "N/A",
        "building": "Maintenance",
        "trade": "Electrician",
        "role": UserRole.STAFF,
        "is_active": True,
    },
}


# =====================================================
# Flask Application Fixture
# =====================================================

@pytest.fixture(scope="session")
def app():
    """
    Creates the Flask application and ensures that the
    dedicated test users exist with the correct credentials.

    Only the dedicated pytest users are created or updated.
    Existing application users are never modified or deleted.
    """

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with flask_app.app_context():

        for user_data in TEST_USERS.values():

            existing_user = User.query.filter_by(
                email=user_data["email"]
            ).first()

            # ---------------------------------------------
            # Create user if it does not already exist
            # ---------------------------------------------

            if existing_user is None:

                new_user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    mobile_number=user_data["mobile_number"],
                    password_hash=generate_password_hash(
                        user_data["password"]
                    ),
                    role=user_data["role"],
                    flat_number=user_data["flat_number"],
                    building=user_data["building"],
                    trade=user_data.get("trade"),
                    is_active=user_data["is_active"],
                )

                db.session.add(new_user)

            # ---------------------------------------------
            # Update only the dedicated test user
            # ---------------------------------------------

            else:

                existing_user.name = user_data["name"]
                existing_user.mobile_number = (
                    user_data["mobile_number"]
                )
                existing_user.password_hash = (
                    generate_password_hash(
                        user_data["password"]
                    )
                )
                existing_user.role = user_data["role"]
                existing_user.flat_number = (
                    user_data["flat_number"]
                )
                existing_user.building = (
                    user_data["building"]
                )
                existing_user.trade = (
                    user_data.get("trade")
                )
                existing_user.is_active = (
                    user_data["is_active"]
                )

        db.session.commit()

        yield flask_app

        db.session.remove()


# =====================================================
# Flask Test Client
# =====================================================

@pytest.fixture(scope="session")
def client(app):
    """
    Returns Flask's test client.
    """

    return app.test_client()


# =====================================================
# Login Helper
# =====================================================

def login(client, credentials):
    """
    Logs in a test user and returns the JWT access token.
    """

    response = client.post(
        "/auth/login",
        json=credentials,
    )

    assert response.status_code == 200, (
        f"Login failed: {response.get_json()}"
    )

    data = response.get_json()

    assert data["success"] is True
    assert "access_token" in data

    return data["access_token"]


# =====================================================
# JWT Token Fixtures
# =====================================================

@pytest.fixture(scope="session")
def admin_token(client):

    return login(
        client,
        {
            "email": TEST_USERS["admin"]["email"],
            "password": TEST_USERS["admin"]["password"],
        },
    )


@pytest.fixture(scope="session")
def resident_token(client):

    return login(
        client,
        {
            "email": TEST_USERS["resident"]["email"],
            "password": TEST_USERS["resident"]["password"],
        },
    )


@pytest.fixture(scope="session")
def staff_token(client):

    return login(
        client,
        {
            "email": TEST_USERS["staff"]["email"],
            "password": TEST_USERS["staff"]["password"],
        },
    )


# =====================================================
# Authorization Header Fixtures
# =====================================================

@pytest.fixture(scope="session")
def admin_headers(admin_token):

    return {
        "Authorization": f"Bearer {admin_token}"
    }


@pytest.fixture(scope="session")
def resident_headers(resident_token):

    return {
        "Authorization": f"Bearer {resident_token}"
    }


@pytest.fixture(scope="session")
def staff_headers(staff_token):

    return {
        "Authorization": f"Bearer {staff_token}"
    }


# =====================================================
# Get an Existing Active Category
# =====================================================

@pytest.fixture(scope="session")
def category_id(app):
    """
    Returns the ID of an existing active category.

    Does not assume that category ID 1 exists.
    """

    from app.models.category import Category

    with app.app_context():

        category = Category.query.filter_by(
            is_active=True
        ).first()

        assert category is not None, (
            "No active category exists in the database. "
            "Create at least one active category before "
            "running pytest."
        )

        return category.id


# =====================================================
# Get Dedicated Test Staff ID
# =====================================================

@pytest.fixture(scope="session")
def staff_user_id(app):
    """
    Returns the database ID of the dedicated test staff user.
    """

    with app.app_context():

        staff = User.query.filter_by(
            email=TEST_USERS["staff"]["email"]
        ).first()

        assert staff is not None, (
            "Dedicated test staff user was not found."
        )

        return staff.id


# =====================================================
# Resident Complaint Fixture
# =====================================================

@pytest.fixture(scope="session")
def resident_complaint(
    client,
    resident_headers,
    category_id,
):
    """
    Creates a complaint using the dedicated test resident
    and returns its complaint ID.
    """

    complaint_data = {
        "category_id": category_id,
        "title": "Pytest Complaint",
        "description": (
            "Complaint created automatically by pytest."
        ),
        "location": "Kitchen",
        "priority": "MEDIUM",
    }

    response = client.post(
        "/complaints",
        json=complaint_data,
        headers=resident_headers,
    )

    assert response.status_code == 201, (
        f"Complaint creation failed: {response.get_json()}"
    )

    data = response.get_json()

    assert data["success"] is True

    return data["complaint"]["id"]


# =====================================================
# Assigned Complaint Fixture
# =====================================================

@pytest.fixture(scope="session")
def assigned_complaint(
    client,
    resident_headers,
    admin_headers,
    category_id,
    staff_user_id,
):
    """
    Creates a complaint using the dedicated test resident
    and assigns it to the dedicated test staff member.
    """

    complaint_data = {
        "category_id": category_id,
        "title": "Assigned Pytest Complaint",
        "description": (
            "Complaint assigned automatically by pytest."
        ),
        "location": "Kitchen",
        "priority": "MEDIUM",
    }

    # ---------------------------------------------
    # Create complaint
    # ---------------------------------------------

    response = client.post(
        "/complaints",
        json=complaint_data,
        headers=resident_headers,
    )

    assert response.status_code == 201, (
        f"Complaint creation failed: {response.get_json()}"
    )

    data = response.get_json()

    assert data["success"] is True

    complaint_id = data["complaint"]["id"]

    # ---------------------------------------------
    # Assign complaint to dedicated test staff
    # ---------------------------------------------

    response = client.put(
        f"/admin/complaints/{complaint_id}/assign",
        headers=admin_headers,
        json={
            "staff_id": staff_user_id,
        },
    )

    assert response.status_code == 200, (
        f"Complaint assignment failed: {response.get_json()}"
    )

    return complaint_id