import requests 
import pytest

BASE_URL = 'http://localhost:8000/api'

# def test_can_create_user():
#     payload = {
#         'email': 'adil@gmail.com',
#         'phone': '+996777212798',
#         "first_name": 'adilhan',
#         "last_name": 'satymkulov',
#         'password' :'Adil2008',
#         'password_confirm' :'Adil2008'
#             }
    
#     res = requests.post(f'{BASE_URL}/auth/register/', json=payload)
#     assert res.status_code == 201
#     assert res.json() 


# def test_can_update_user():
#     payload = {
#         'email': 'danielsatymkulov40@gmail.com',
#         'phone': '+996777212798',
#         "first_name": 'adilhan',
#         "last_name": 'bakytbek',
#         'password' :'Adil2008',
#         'password_confirm' :'Adil2008'
#             }
    
#     res = requests.put(f'{BASE_URL}/auth/update/1', json=payload)
#     assert res.json() 


# def test_can_login():
#     payload = {
#         "email": 'danielsatymkulov40@gmail.com',
#         "password": 'Adil2008'
#     }

#     res = requests.post(f'{BASE_URL}/auth/login/', json=payload)
#     assert res.json()
#     assert 1 == 0


# def test_can_refresh_access_token():
#     payload = {
#         'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3MTIzNzA1OSwiaWF0IjoxNzcxMTUwNjU5LCJqdGkiOiI0ODA4Mzc0ZGYxZjM0NWE1YTZiMTE3YzU5OWFhNjkyYiIsInVzZXJfaWQiOiIxIn0.HXpWaJbtafizZxmU2I68HTe3OUxCBL2gZdlt0iDc9bw'
#     }

#     res = requests.post(f'{BASE_URL}/auth/token/refresh/', json=payload)
#     assert 1 ==0

# def test_can_get_me_user():
#     # 1. Логинимся (используем данные из теста регистрации)
#     login_payload = {
#         'email': 'adilhansatymkulov40@gmail.com',
#         'password': 'Adil2008'
#     }
#     login_res = requests.post(f'{BASE_URL}/auth/login/', json=login_payload)
    
#     # 2. Извлекаем токен из ВАШЕЙ новой структуры {'tokens': {'access': '...'}}
#     access_token = login_res.json()['tokens']['access']
    
#     # 3. Делаем запрос к /me/ с заголовком Authorization
#     headers = {'Authorization': f'Bearer {access_token}'}
#     res = requests.get(f'{BASE_URL}/auth/me/', headers=headers)
    
#     # 4. Проверяем результат
#     assert res.status_code == 200
#     assert res.json()['email'] == login_payload['email']
#     assert 'first_name' in res.json()


def test_can_get_me_user():
    # 1. Логинимся (используем данные из теста регистрации)
    login_payload = {
        'email': 'adilhansatymkulov40@gmail.com',
        'password': 'Adil2008'
    }
    login_res = requests.post(f'{BASE_URL}/auth/login/', json=login_payload)
    
    # 2. Извлекаем токен из ВАШЕЙ новой структуры {'tokens': {'access': '...'}}
    access_token = login_res.json()['tokens']['access']
    refresh_token = login_res.json()['tokens']['refresh']
    logout_payload = {
        'refresh': refresh_token
    }

    
    # 3. Делаем запрос к /me/ с заголовком Authorization
    headers = {'Authorization': f'Bearer {access_token}'}
    res = requests.post(f'{BASE_URL}/auth/logout/', headers=headers, json=logout_payload)
    
    # 4. Проверяем результат
    assert res.status_code == 205

