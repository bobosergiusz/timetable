from datetime import datetime
import pytest

from timetable.adapters.repository import DoesNotExistsError
from timetable.domain.accept import NotAvailableError
from timetable.service_layer.services import (
    accept_appointment,
    ask_appointment,
    list_appointments,
    create_client,
    create_service,
    get_user,
)


class FakeRepository:
    def __init__(self, apps):
        self.apps = apps

    def get(self, id):
        app = next((a for a in self.apps if a.id == id), None)
        if app is None:
            raise DoesNotExistsError
        return app

    def list(self):
        return self.apps

    def add(self, app):
        id = len(self.apps)
        app.id = id
        self.apps.append(app)


class FakeUsersRepository:
    def __init__(self, users):
        self.users = users

    def get(self, id):
        user = next((u for u in self.users if u.account_name == id), None)
        if user is None:
            raise DoesNotExistsError
        return user

    def list(self):
        return self.users

    def add(self, user):
        user_saved = next(
            (u for u in self.users if u.account_name == id), None
        )
        if user_saved is not None:
            self.users.remove(user_saved)
        self.users.append(user)


class FakeUnitOfWork:
    def __init__(self):
        self.commited = False
        self.appointments = FakeRepository([])
        self.users = FakeUsersRepository([])

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def rollback(self):
        pass

    def commit(self):
        self.commited = True


def test_ask_appoinment_creates_when_free():
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)

    uow = FakeUnitOfWork()
    app_returned = ask_appointment(since, until, uow)

    app_stored = uow.appointments.list().pop().to_dict()
    assert app_returned["since"] == since
    assert app_returned["until"] == until
    assert not app_returned["accepted"]
    assert app_stored["since"] == since
    assert app_stored["until"] == until
    assert not app_stored["accepted"]
    assert uow.commited


def test_accept_ok_when_free():
    uow = FakeUnitOfWork()
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    app_returned_unaccepted = ask_appointment(since, until, uow)
    id = app_returned_unaccepted["id"]

    uow.commited = False
    app_returned = accept_appointment(id, uow)

    app_stored = uow.appointments.list().pop().to_dict()
    assert app_returned["since"] == since
    assert app_returned["until"] == until
    assert app_returned["accepted"]
    assert app_stored["since"] == since
    assert app_stored["until"] == until
    assert app_stored["accepted"]
    assert uow.commited


def test_ask_appoinment_cannot_create_when_occupied():
    uow = FakeUnitOfWork()
    since1 = datetime(2000, 1, 1, 1)
    until1 = datetime(2000, 1, 1, 4)
    app_returned_unaccepted1 = ask_appointment(since1, until1, uow)
    id = app_returned_unaccepted1["id"]
    accept_appointment(id, uow)

    since = datetime(2000, 1, 1, 2)
    until = datetime(2000, 1, 1, 3)

    uow.commited = False
    with pytest.raises(NotAvailableError):
        ask_appointment(since, until, uow)
    assert not uow.commited


def test_accept_bad_when_occupied():
    uow = FakeUnitOfWork()
    since1 = datetime(2000, 1, 1, 1)
    until1 = datetime(2000, 1, 1, 4)
    app_returned_unaccepted1 = ask_appointment(since1, until1, uow)
    id1 = app_returned_unaccepted1["id"]
    app_returned_unaccepted2 = ask_appointment(since1, until1, uow)
    id2 = app_returned_unaccepted2["id"]
    accept_appointment(id1, uow)

    uow.commited = False
    with pytest.raises(NotAvailableError):
        accept_appointment(id2, uow)
    assert not uow.commited


def test_accept_when_wrong_id():
    uow = FakeUnitOfWork()
    since1 = datetime(2000, 1, 1, 1)
    until1 = datetime(2000, 1, 1, 4)
    app_returned_unaccepted1 = ask_appointment(since1, until1, uow)
    id = app_returned_unaccepted1["id"]

    uow.commited = False
    with pytest.raises(DoesNotExistsError):
        accept_appointment(id + 1, uow)
    assert not uow.commited


def test_list_returns_all():
    uow = FakeUnitOfWork()
    since1 = datetime(2000, 1, 1, 1)
    until1 = datetime(2000, 1, 1, 4)
    app1 = ask_appointment(since1, until1, uow)
    since2 = datetime(2000, 1, 2, 1)
    until2 = datetime(2000, 1, 2, 4)
    app2 = ask_appointment(since2, until2, uow)
    id2 = app2["id"]
    app2_accepted = accept_appointment(id2, uow)
    uow.commited = False
    [app1_returned, app2_returned] = list_appointments(uow)
    assert app1_returned == app1
    assert app2_returned == app2_accepted
    assert not uow.commited


def test_create_client():
    uow = FakeUnitOfWork()
    account_name = "bob"
    email = "bob@dot.com"
    password = "123"
    u = create_client(account_name, email, password, uow)
    assert u["account_name"] == account_name
    assert u["email"] == email
    assert u["password"] == password
    assert uow.commited
    user_stored = uow.users.list().pop().to_dict()
    assert user_stored["account_name"] == account_name
    assert user_stored["email"] == email
    assert user_stored["password"] == password


def test_cannot_create_client_with_existing_account_name():
    uow = FakeUnitOfWork()
    account_name = "bob"
    email = "bob@dot.com"
    password = "123"
    create_client(account_name, email, password, uow)
    uow.commited = False
    with pytest.raises(NotAvailableError):
        create_client(account_name, email, password, uow)
    assert not uow.commited


def test_create_service():
    uow = FakeUnitOfWork()
    account_name = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["warsaw", "mechanic"]
    u = create_service(account_name, email, password, tags, uow)
    assert u["account_name"] == account_name
    assert u["email"] == email
    assert u["password"] == password
    assert u["tags"] == tags
    assert uow.commited
    user_stored = uow.users.list().pop().to_dict()
    assert user_stored["account_name"] == account_name
    assert user_stored["email"] == email
    assert user_stored["password"] == password
    assert user_stored["tags"] == tags


def test_cannot_create_user_with_existing_account_name():
    uow = FakeUnitOfWork()
    account_name = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["warsaw", "mechanic"]
    create_service(account_name, email, password, tags, uow)
    uow.commited = False
    with pytest.raises(NotAvailableError):
        create_service(account_name, email, password, tags, uow)
    assert not uow.commited


def test_get_existing_user():
    uow = FakeUnitOfWork()
    account_name = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["warsaw", "mechanic"]
    create_service(account_name, email, password, tags, uow)
    uow.commited = False
    u = get_user(account_name, uow)
    assert u["account_name"] == account_name
    assert u["email"] == email
    assert u["password"] == password
    assert u["tags"] == tags
    assert not uow.commited


def test_cannot_get_unexisting_user():
    uow = FakeUnitOfWork()
    account_name = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["warsaw", "mechanic"]
    create_service(account_name, email, password, tags, uow)
    uow.commited = False
    with pytest.raises(DoesNotExistsError):
        get_user("john", uow)
    assert not uow.commited
