import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        # Add mock users
        user1 = User(username='testuser1', email='test1@example.com', password_hash='test')
        user2 = User(username='testuser2', email='test2@example.com', password_hash='test')
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
        assert res.status_code == 200
        assert len(res.json) == 2
