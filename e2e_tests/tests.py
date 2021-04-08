from datetime import datetime
import os

import requests


def get_api_url():
    host = os.environ.get("API_HOST")
    port = os.environ.get("API_PORT")
    return f"http://{host}:{port}"


def create_client(account_name, password, email, s):
    api_url = get_api_url()
    json = {
        "account_name": account_name,
        "password": password,
        "email": email,
        "account_type": "client",
    }
    resp = s.post(f"{api_url}/user", json=json)
    return resp


def get_client(account_name, s):
    api_url = get_api_url()
    resp = s.get(f"{api_url}/user/{account_name}")
    return resp


def create_service(account_name, password, email, tags, s):
    api_url = get_api_url()

    json = {
        "account_name": account_name,
        "password": password,
        "email": email,
        "account_type": "service",
        "tags": tags,
    }
    resp = s.post(f"{api_url}/user", json=json)
    assert resp


def login(account_name, password, s):
    api_url = get_api_url()
    json = {"account_name": account_name, "password": password}
    resp = s.post(f"{api_url}/login", json=json)
    return resp


def get_csfr_token(resp):
    s = resp.headers["Set-Cookie"]
    _, data = s.split("csrf_access_token=")
    cookie, _ = data.split(";")
    return cookie


def logout(s):
    api_url = get_api_url()
    resp = s.post(f"{api_url}/logout")
    return resp


def create_appointment(to_user, since, until, description, csfr_token, s):
    api_url = get_api_url()
    json = {
        "since": since,
        "until": until,
        "description": description,
    }
    headers = {
        "X-CSRF-TOKEN": csfr_token,
    }

    resp = s.post(
        f"{api_url}/service/{to_user}/appointment", json=json, headers=headers
    )
    return resp


def get_appointment_detail(to_user, app_id, csfr_token, s):
    api_url = get_api_url()
    headers = {
        "X-CSRF-TOKEN": csfr_token,
    }

    resp = s.get(
        f"{api_url}/service/{to_user}/appointment/{app_id}",
        headers=headers,
    )
    return resp


def accept_appointment(to_user, app_id, csfr_token, s):
    api_url = get_api_url()
    headers = {
        "X-CSRF-TOKEN": csfr_token,
    }

    resp = s.put(
        f"{api_url}/service/{to_user}/appointment/{app_id}",
        headers=headers,
    )
    return resp


def get_appointments(to_user, csfr_token, s):
    api_url = get_api_url()
    headers = {
        "X-CSRF-TOKEN": csfr_token,
    }

    resp = s.get(
        f"{api_url}/service/{to_user}/appointment",
        headers=headers,
    )
    return resp


def test_create_user_get_user_happy():
    account_name = "bob"
    password = "123"
    email = "bob@dot.com"
    resp_post = create_client(account_name, password, email, requests)
    assert resp_post.status_code == 201

    resp_get = get_client(account_name, requests)
    u = resp_get.json()
    assert resp_get.status_code == 200
    assert u["account_name"] == account_name
    assert u["email"] == email


def test_create_user_unhappy():
    account_name = "john"
    password = "123"
    email = "john@dot.com"
    create_client(account_name, password, email, requests)
    resp = create_client(account_name, password, email, requests)
    assert resp.status_code == 400


def test_login_user_happy():
    account_name = "katie"
    password = "123"
    email = "katie@dot.com"
    create_client(account_name, password, email, requests)
    resp = login(account_name, password, requests)
    assert resp.status_code == 200


def test_login_user_unhappy():
    account_name = "joe"
    password = "123"
    email = "joe@dot.com"
    wrong_password = "456"
    create_client(account_name, password, email, requests)
    resp = login(account_name, wrong_password, requests)
    assert resp.status_code == 400


def test_list_services():
    api_url = get_api_url()
    tags = ["medical", "health"]

    account_name1 = "doctor1"
    password1 = "123"
    email1 = "doctor1@dot.com"
    tags1 = tags + ["warsaw"]
    create_service(account_name1, password1, email1, tags1, requests)

    account_name2 = "doctor2"
    password2 = "123"
    email2 = "doctor2@dot.com"
    tags2 = tags + ["lodz"]
    create_service(account_name2, password2, email2, tags2, requests)

    account_name3 = "mechanic"
    password3 = "123"
    email3 = "mechanic@dot.com"
    tags3 = ["car", "mechanic", "lodz"]
    create_service(account_name3, password3, email3, tags3, requests)

    resp1 = requests.get(f"{api_url}/service", params={"tags": ",".join(tags)})
    assert resp1.status_code == 200
    assert resp1.json() == [
        {"account_name": account_name1, "tags": tags1},
        {"account_name": account_name2, "tags": tags2},
    ]
    resp2 = requests.get(f"{api_url}/service")
    assert resp2.status_code == 200
    assert resp2.json() == [
        {"account_name": account_name1, "tags": tags1},
        {"account_name": account_name2, "tags": tags2},
        {"account_name": account_name3, "tags": tags3},
    ]


def test_create_appointment_get_appointment_detail_happy():
    account_name_s = "barber"
    password_s = "123"
    email_s = "barber@dot.com"
    tags_s = ["barber", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "sean"
    password_c = "345"
    email_c = "sean@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    description = "haircut"
    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        csfr_token_c = get_csfr_token(resp_login_c)
        resp_create = create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    assert resp_create.status_code == 201

    app_model = {
        "from_user": account_name_c,
        "since": since,
        "until": until,
        "description": description,
        "accepted": False,
    }

    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_list = get_appointments(account_name_s, csfr_token_s, s)
        [app] = resp_list.json()
        resp_get = get_appointment_detail(
            account_name_s, app["id"], csfr_token_s, s
        )
    assert resp_get.status_code == 200
    app_get = resp_get.json()
    del app_get["id"]
    assert app_get == app_model


def test_create_appointment_unhappy():
    account_name_s = "barber2"
    password_s = "123"
    email_s = "barber2@dot.com"
    tags_s = ["barber", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "sean2"
    password_c = "345"
    email_c = "sean2@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        csfr_token_c = get_csfr_token(resp_login_c)
        since = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        description = "haircut"
        resp_create = create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    assert resp_create.status_code == 400


def test_get_appointment_detail_unhappy():
    account_name_s = "boxing-training"
    password_s = "123"
    email_s = "boxing@dot.com"
    tags_s = ["sport", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "persival"
    password_c = "345"
    email_c = "persival@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "sparing"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_list = get_appointments(account_name_s, csfr_token_s, s)
        [app_unaccepted] = resp_list.json()
        id_ = app_unaccepted["id"]
        resp_get = get_appointment_detail(
            account_name_s, id_ + 1, csfr_token_s, s
        )
    assert resp_get.status_code == 400


def test_accept_appointment_happy():
    account_name_s = "beauty_salon"
    password_s = "123"
    email_s = "beauty_salon@dot.com"
    tags_s = ["beauty_salon", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "matilda"
    password_c = "345"
    email_c = "matilda@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)

        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "haircut"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_list = get_appointments(account_name_s, csfr_token_s, s)
        [app_unaccepted] = resp_list.json()
        id_ = app_unaccepted["id"]
        resp_accept = accept_appointment(account_name_s, id_, csfr_token_s, s)
        resp_get = get_appointment_detail(account_name_s, id_, csfr_token_s, s)
    assert resp_accept.status_code == 200
    app_accepted = resp_get.json()
    assert app_accepted["accepted"]
    del app_accepted["accepted"]
    del app_unaccepted["accepted"]
    assert app_accepted == app_unaccepted


def test_accept_appointment_unhappy():
    account_name_s = "hairdresser"
    password_s = "123"
    email_s = "hairdresser@dot.com"
    tags_s = ["hairdresser", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "elizabeth"
    password_c = "345"
    email_c = "elizabeth@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)

        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "haircut"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_list = get_appointments(account_name_s, csfr_token_s, s)
        [app_unaccepted] = resp_list.json()
        id_ = app_unaccepted["id"]
    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        csfr_token_c = get_csfr_token(resp_login_c)
        resp_accept = accept_appointment(account_name_s, id_, csfr_token_c, s)
    assert resp_accept.status_code == 401


def test_get_appointment_own():
    account_name_s = "hairdresser3"
    password_s = "123"
    email_s = "hairdresser3@dot.com"
    tags_s = ["hairdresser", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "elizabeth3"
    password_c = "345"
    email_c = "elizabeth3@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)

        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "haircut"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )

    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_get = get_appointments(account_name_s, csfr_token_s, s)
    assert resp_get.status_code == 200
    app_model = {
        "from_user": account_name_c,
        "since": since,
        "until": until,
        "description": description,
        "accepted": False,
    }
    [app] = resp_get.json()
    del app["id"]
    assert app == app_model


def test_get_appointment_unown():
    account_name_s = "hairdresser4"
    password_s = "123"
    email_s = "hairdresser4@dot.com"
    tags_s = ["sport", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "elizabeth4"
    password_c = "345"
    email_c = "elizabeth4@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "haircut"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_list = get_appointments(account_name_s, csfr_token_s, s)
        [app_unaccepted] = resp_list.json()
        id_ = app_unaccepted["id"]
        accept_appointment(account_name_s, id_, csfr_token_s, s)
    with requests.Session() as s:
        resp_login_c2 = login(account_name_c, password_c, s)
        csfr_token_c2 = get_csfr_token(resp_login_c2)
        resp_get = get_appointments(account_name_s, csfr_token_c2, s)
    expected = {"since": since, "until": until}
    assert resp_get.status_code == 200
    assert resp_get.json() == [expected]


def test_get_appointment_unhappy():
    account_name_s = "music-lessons"
    password_s = "123"
    email_s = "music@dot.com"
    tags_s = ["music", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "alan"
    password_c = "345"
    email_c = "alan@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "lesson"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )

    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        account_name_wrong = "wrong_name"
        resp_get = get_appointments(account_name_wrong, csfr_token_s, s)
    assert resp_get.status_code == 400


def test_logout():
    account_name_s = "soccer-training"
    password_s = "123"
    email_s = "soccer@dot.com"
    tags_s = ["sport", "warsaw"]
    create_service(account_name_s, password_s, email_s, tags_s, requests)

    account_name_c = "ryan"
    password_c = "345"
    email_c = "ryan@dot.com"
    create_client(account_name_c, password_c, email_c, requests)

    with requests.Session() as s:
        resp_login_c = login(account_name_c, password_c, s)
        since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
        until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
        description = "dribbling-training"
        csfr_token_c = get_csfr_token(resp_login_c)
        create_appointment(
            account_name_s, since, until, description, csfr_token_c, s
        )
    with requests.Session() as s:
        resp_login_s = login(account_name_s, password_s, s)
        csfr_token_s = get_csfr_token(resp_login_s)
        resp_list = get_appointments(account_name_s, csfr_token_s, s)
        [app_unaccepted] = resp_list.json()
        id_ = app_unaccepted["id"]
        resp_get = get_appointment_detail(account_name_s, id_, csfr_token_s, s)
        assert resp_get.status_code == 200
        resp_logout = logout(s)
        assert resp_get.status_code == 200
        assert resp_logout.json() == {"msg": "logout successful"}
        resp_get2 = get_appointment_detail(
            account_name_s, id_, csfr_token_s, s
        )
        assert resp_get2.status_code == 401
