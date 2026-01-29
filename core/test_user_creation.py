import pytest
import requests

url = 'http://localhost:8000/api/create-user'

def test_create_user():
    payload = {
        "email": "AdilhanSatymkulov40@gmail.com",
        "first_name": "adilhan",
        "last_name": "AdilhanSatymkulov40@gmail.com",
        "password": "Adil2008!"
    }

    res = requests.post(url, json=payload)
    data = res.json()

    assert res.status_code == 201
    assert data["email"] == 'AdilhanSatymkulov40@gmail.com'
    assert data["first_name"] == 'adilhan'
    