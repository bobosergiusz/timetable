from datetime import datetime
import os

import requests


def get_api_url():
    host = os.environ.get("API_HOST")
    port = os.environ.get("API_PORT")
    return f"http://{host}:{port}"


def create_client(account_name, password, email):
    api_url = get_api_url()
    json = {
        "account_name": account_name,
        "password": password,
        "email": email,
        "account_type": "client",
    }
    resp = requests.post(f"{api_url}/user", json=json)
    return resp


def create_service(account_name, password, email, tags):
    api_url = get_api_url()

    json = {
        "account_name": account_name,
        "password": password,
        "email": email,
        "account_type": "service",
        "tags": tags,
    }
    resp = requests.post(f"{api_url}/user", json=json)
    assert resp


def login(account_name, password):
    api_url = get_api_url()
    json = {"account_name": account_name, "password": password}
    resp = requests.post(f"{api_url}/login", json=json)
    return resp


def create_appointment(to_user, since, until, description, access_token):
    api_url = get_api_url()
    json = {
        "since": since,
        "until": until,
        "description": description,
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.post(
        f"{api_url}/service/{to_user}/appointment", json=json, headers=headers
    )
    return resp


def get_appointment_detail(to_user, app_id, access_token):
    api_url = get_api_url()
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        f"{api_url}/service/{to_user}/appointment/{app_id}",
        headers=headers,
    )
    return resp


def accept_appointment(to_user, app_id, access_token):
    api_url = get_api_url()
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.put(
        f"{api_url}/service/{to_user}/appointment/{app_id}",
        headers=headers,
    )
    return resp


def get_appointments(to_user, access_token):
    api_url = get_api_url()
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(
        f"{api_url}/service/{to_user}/appointment",
        headers=headers,
    )
    return resp


def test_create_user_happy():
    account_name = "bob"
    password = "123"
    email = "bob@dot.com"
    resp = create_client(account_name, password, email)
    assert resp.status_code == 201
    u = resp.json()
    assert u["account_name"] == account_name
    assert u["password"] == password
    assert u["email"] == email


def test_create_user_unhappy():
    account_name = "john"
    password = "123"
    email = "john@dot.com"
    create_client(account_name, password, email)
    resp = create_client(account_name, password, email)
    assert resp.status_code == 400


def test_login_user_happy():
    account_name = "katie"
    password = "123"
    email = "katie@dot.com"
    create_client(account_name, password, email)
    resp = login(account_name, password)
    assert resp.json()["access_token"]
    assert resp.status_code == 200


def test_login_user_unhappy():
    account_name = "joe"
    password = "123"
    email = "joe@dot.com"
    wrong_password = "456"
    create_client(account_name, password, email)
    resp = login(account_name, wrong_password)
    assert resp.status_code == 400


def test_list_services():
    api_url = get_api_url()
    tags = ["medical", "health"]

    account_name1 = "doctor1"
    password1 = "123"
    email1 = "doctor1@dot.com"
    tags1 = tags + ["warsaw"]
    create_service(account_name1, password1, email1, tags1)

    account_name2 = "doctor2"
    password2 = "123"
    email2 = "doctor2@dot.com"
    tags2 = tags + ["lodz"]
    create_service(account_name2, password2, email2, tags2)

    account_name3 = "mechanic"
    password3 = "123"
    email3 = "mechanic@dot.com"
    tags3 = ["car", "mechanic", "lodz"]
    create_service(account_name3, password3, email3, tags3)

    resp = requests.get(f"{api_url}/service", params={"tags": ",".join(tags)})
    assert resp.status_code == 200
    assert resp.json() == [
        {"account_name": account_name1, "tags": tags1},
        {"account_name": account_name2, "tags": tags2},
    ]
    resp = requests.get(f"{api_url}/service")
    assert resp.status_code == 200
    assert resp.json() == [
        {"account_name": account_name1, "tags": tags1},
        {"account_name": account_name2, "tags": tags2},
        {"account_name": account_name3, "tags": tags3},
    ]


def test_create_appointment_get_appointment_detail_happy():
    account_name_s = "barber"
    password_s = "123"
    email_s = "barber@dot.com"
    tags_s = ["barber", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "sean"
    password_c = "345"
    email_c = "sean@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    access_token = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token
    )
    app_created = resp_create.json()
    id_ = app_created["id"]
    role_model = {
        "id": id_,
        "from_user": account_name_c,
        "since": since,
        "until": until,
        "description": description,
        "accepted": False,
    }
    assert resp_create.json() == role_model
    assert resp_create.status_code == 201

    resp_login_s = login(account_name_s, password_s)
    access_token = resp_login_s.json()["access_token"]
    resp_get = get_appointment_detail(account_name_s, id_, access_token)
    assert resp_get.json() == role_model
    assert resp_get.status_code == 200


def test_create_appointment_unhappy():
    account_name_s = "barber2"
    password_s = "123"
    email_s = "barber2@dot.com"
    tags_s = ["barber", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "sean2"
    password_c = "345"
    email_c = "sean2@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    access_token = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token
    )
    assert resp_create.status_code == 400


def test_accept_appointment_happy():
    account_name_s = "beauty_salon"
    password_s = "123"
    email_s = "beauty_salon@dot.com"
    tags_s = ["beauty_salon", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "matilda"
    password_c = "345"
    email_c = "matilda@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    access_token = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token
    )
    id_ = resp_create.json()["id"]
    resp_login_s = login(account_name_s, password_s)
    access_token = resp_login_s.json()["access_token"]
    resp_accept = accept_appointment(account_name_s, id_, access_token)
    resp_get = get_appointment_detail(account_name_s, id_, access_token)
    assert resp_accept.json()["accepted"]
    assert resp_accept.status_code == 200
    assert resp_get.json()["accepted"]


def test_accept_appointment_unhappy():
    account_name_s = "hairdresser"
    password_s = "123"
    email_s = "hairdresser@dot.com"
    tags_s = ["hairdresser", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "elizabeth"
    password_c = "345"
    email_c = "elizabeth@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    access_token = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token
    )
    id_ = resp_create.json()["id"]
    resp_accept = accept_appointment(account_name_s, id_, access_token)
    assert resp_accept.status_code == 401


def test_get_appointment_own():
    account_name_s = "hairdresser3"
    password_s = "123"
    email_s = "hairdresser3@dot.com"
    tags_s = ["hairdresser", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "elizabeth3"
    password_c = "345"
    email_c = "elizabeth3@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    access_token = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token
    )
    resp_login_s = login(account_name_s, password_s)
    access_token = resp_login_s.json()["access_token"]
    resp_get = get_appointments(account_name_s, access_token)
    assert resp_get.status_code == 200
    assert resp_get.json() == [resp_create.json()]


def test_get_appointment_unown():
    account_name_s = "hairdresser4"
    password_s = "123"
    email_s = "hairdresser4@dot.com"
    tags_s = ["sport", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "elizabeth4"
    password_c = "345"
    email_c = "elizabeth4@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    access_token_c = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token_c
    )
    id_ = resp_create.json()["id"]
    resp_login_s = login(account_name_s, password_s)
    access_token_s = resp_login_s.json()["access_token"]
    accept_appointment(account_name_s, id_, access_token_s)
    resp_get = get_appointments(account_name_s, access_token_c)
    expected = {"since": since, "until": until}
    assert resp_get.status_code == 200
    assert resp_get.json() == [expected]


def test_get_appointment_unhappy():
    account_name_s = "music-lessons"
    password_s = "123"
    email_s = "music@dot.com"
    tags_s = ["music", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "alan"
    password_c = "345"
    email_c = "alan@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "lesson"
    access_token_c = resp_login_c.json()["access_token"]
    create_appointment(
        account_name_s, since, until, description, access_token_c
    )

    resp_login_s = login(account_name_s, password_s)
    access_token_s = resp_login_s.json()["access_token"]
    account_name_wrong = "wrong_name"
    resp_get = get_appointments(account_name_wrong, access_token_s)
    assert resp_get.status_code == 400


def test_get_appointment_detail_unhappy():
    account_name_s = "boxing-training"
    password_s = "123"
    email_s = "boxing@dot.com"
    tags_s = ["sport", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s)

    account_name_c = "persival"
    password_c = "345"
    email_c = "persival@dot.com"
    create_client(account_name_c, password_c, email_c)

    resp_login_c = login(account_name_c, password_c)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "sparing"
    access_token_c = resp_login_c.json()["access_token"]
    resp_create = create_appointment(
        account_name_s, since, until, description, access_token_c
    )
    id_ = resp_create.json()["id"]
    resp_login_s = login(account_name_s, password_s)
    access_token_s = resp_login_s.json()["access_token"]
    resp_get = get_appointment_detail(account_name_s, id_ + 1, access_token_s)
    assert resp_get.status_code == 400
