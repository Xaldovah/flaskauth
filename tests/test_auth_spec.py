import pytest
from flask import url_for
from app import app, db
from models import User, Organisation
from datetime import datetime, timedelta
import jwt

@pytest.fixture
def client():
    return app.test_client()


@pytest.mark.parametrize("data, status_code", [
    ({"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "password": "password", "phone": "123456789"}, 201),
    ({"first_name": "John", "email": "john.doe@example.com", "password": "password"}, 422),
    ({"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "password": "password"}, 422)
])

def test_register(client, data, status_code):
    response = client.post(url_for('register'), json=data)
    assert response.status_code == status_code

def test_login(client):
    user = User(first_name="John", last_name="Doe", email="john.doe@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    response = client.post(url_for('login'), json={"email": "john.doe@example.com", "password": "password"})
    assert response.status_code == 200
    assert "accessToken" in response.get_json()["data"]

def test_get_user(client):
    user = User(first_name="John", last_name="Doe", email="john.doe@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    access_token = jwt.encode({"user_id": str(user.user_id), "exp": datetime.utcnow() + timedelta(hours=1)}, app.config["JWT_SECRET_KEY"], algorithm="HS256")
    response = client.get(url_for('get_user', user_id=user.user_id), headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == "john.doe@example.com"
