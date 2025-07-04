import pytest
import os
import hashlib
from app import create_app, db
from app.models import User
from tests.security_test_utils import SecureTestUtils, secure_equal, secure_status, secure_length, secure_no_sensitive

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        # Add mock users with secure test password handling
        password_hash = SecureTestUtils.get_test_password_hash()
        
        user1 = User(username='testuser1', email='test1@example.com', password_hash=password_hash)
        user2 = User(username='testuser2', email='test2@example.com', password_hash=password_hash)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_users(client, app):
    with app.app_context():
        res = client.get("/api/users")
        
        # Use secure assertions instead of assert statements
        secure_status(res, 200, "API should return 200 OK")
        secure_length(res.json, 2, "Should return exactly 2 users")
        
        # Additional validation for security
        if not res.json:
            pytest.fail("Response JSON is empty")
        
        # Verify response structure and security
        sensitive_fields = ['password_hash', 'password', 'secret', 'token']
        for user in res.json:
            secure_no_sensitive(user, sensitive_fields, "User data should not expose sensitive fields")
