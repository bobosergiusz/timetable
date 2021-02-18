from datetime import datetime
import os

import requests


def get_api_url():
    host = os.environ.get("API_HOST")
    port = os.environ.get("API_PORT")
    return f"http://{host}:{port}"


def test_appointments_list():
    api_url = get_api_url()
    resp = requests.get(f"{api_url}/appointment")
    assert isinstance(resp.json(), list)
    assert resp.status_code == 200


def test_appointments_post_happy():
    api_url = get_api_url()
    resp1 = requests.get(f"{api_url}/appointment")
    list_pre = resp1.json()
    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    json = {
        "since": since,
        "until": until,
    }
    resp = requests.post(f"{api_url}/appointment", json=json)
    resp2 = requests.get(f"{api_url}/appointment")
    list_post = resp2.json()
    assert len(list_post) == len(list_pre) + 1
    set_pre = set(j["id"] for j in list_pre)
    set_post = set(j["id"] for j in list_post)
    assert len(set_post) == len(set_pre) + 1
    assert len(set_pre) == len(list_pre)
    # TODO: eventually could also check if the rest of returned list is
    # unchanged
    id = set_post.difference(set_pre).pop()
    added = next(a for a in list_post if a["id"] == id)
    assert added == {
        "id": id,
        "accepted": False,
        "since": since,
        "until": until,
    }
    assert added == resp.json()
    assert resp.status_code == 201


def test_appointments_put_happy():
    api_url = get_api_url()
    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    json = {
        "since": since,
        "until": until,
    }
    resp_pre = requests.post(f"{api_url}/appointment", json=json)
    id = resp_pre.json()["id"]
    resp1 = requests.get(f"{api_url}/appointment")
    list_pre = resp1.json()
    resp_post = requests.put(f"{api_url}/appointment/{id}", json=json)
    resp2 = requests.get(f"{api_url}/appointment")
    list_post = resp2.json()
    assert len(list_post) == len(list_pre)
    set_pre = set(j["id"] for j in list_pre)
    set_post = set(j["id"] for j in list_post)
    assert len(set_post) == len(set_pre)
    assert len(set_pre) == len(list_pre)
    # TODO: eventually could also check if the rest of returned list is
    # unchanged
    changed = next(a for a in list_post if a["id"] == id)
    assert changed == {
        "id": id,
        "accepted": True,
        "since": since,
        "until": until,
    }
    assert changed == resp_post.json()
    assert resp_post.status_code == 200


def test_appointments_post_unhappy():
    api_url = get_api_url()
    since = datetime(2000, 1, 1, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 1, 2, 1).strftime("%Y-%m-%d %H:%M")
    json = {
        "since": since,
        "until": until,
    }
    requests.post(f"{api_url}/appointment", json=json)
    resp = requests.post(f"{api_url}/appointment", json=json)
    assert resp.status_code == 400


def test_appointments_put_unhappy():
    api_url = get_api_url()
    since = datetime(2000, 1, 2, 1, 0).strftime("%Y-%m-%d %H:%M")
    until = datetime(2000, 1, 2, 2, 1).strftime("%Y-%m-%d %H:%M")
    json = {
        "since": since,
        "until": until,
    }
    resp1 = requests.post(f"{api_url}/appointment", json=json)
    id1 = resp1.json()["id"]
    resp2 = requests.post(f"{api_url}/appointment", json=json)
    id2 = resp2.json()["id"]
    requests.put(f"{api_url}/appointment/{id1}", json=json)
    resp = requests.put(f"{api_url}/appointment/{id2}", json=json)
    assert resp.status_code == 400
