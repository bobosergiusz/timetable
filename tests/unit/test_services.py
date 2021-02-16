from datetime import datetime
import pytest

from timetable.adapters.repository import DoesNotExistsError
from timetable.domain.accept import NotAvailableError
from timetable.service_layer.services import (
    accept_appointment,
    ask_appointment,
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


class FakeUnitOfWork:
    def __init__(self):
        self.commited = False
        self.appointments = FakeRepository([])

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

    app_stored = uow.appointments.list().pop()
    assert app_returned.since == since
    assert app_returned.until == until
    assert not app_returned.accepted
    assert app_stored.since == since
    assert app_stored.until == until
    assert not app_stored.accepted
    assert uow.commited


def test_accept_ok_when_free():
    uow = FakeUnitOfWork()
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    app_returned_unaccepted = ask_appointment(since, until, uow)
    id = app_returned_unaccepted.id

    uow.commited = False
    app_returned = accept_appointment(id, uow)

    app_stored = uow.appointments.list().pop()
    assert app_returned.since == since
    assert app_returned.until == until
    assert app_returned.accepted
    assert app_stored.since == since
    assert app_stored.until == until
    assert app_stored.accepted
    assert uow.commited


def test_ask_appoinment_cannot_create_when_occupied():
    uow = FakeUnitOfWork()
    since1 = datetime(2000, 1, 1, 1)
    until1 = datetime(2000, 1, 1, 4)
    app_returned_unaccepted1 = ask_appointment(since1, until1, uow)
    id = app_returned_unaccepted1.id
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
    id1 = app_returned_unaccepted1.id
    app_returned_unaccepted2 = ask_appointment(since1, until1, uow)
    id2 = app_returned_unaccepted2.id
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
    id = app_returned_unaccepted1.id

    uow.commited = False
    with pytest.raises(DoesNotExistsError):
        accept_appointment(id + 1, uow)
    assert not uow.commited
