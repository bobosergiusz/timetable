from datetime import datetime
from random import randint

import pytest
from tests.fakes import FakeUnitOfWork

from timetable.domain.command import (
    CreateClient,
    CreateService,
    CreateAppointment,
    AcceptAppointment,
)
from timetable.service_layer.message_bus import MessageBus
from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError


class TestCreateUser:
    def test_create_client(self):
        uow = FakeUnitOfWork()
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        cu = CreateClient(account_name, email, password)
        mb = MessageBus()
        mb.handle(cu, uow)
        assert uow.commited
        user_stored = uow.users.list().pop().to_dict()
        assert user_stored["account_name"] == account_name
        assert user_stored["email"] == email
        assert user_stored["password"] == password

    def test_cannot_create_client_with_existing_account_name(self):
        uow = FakeUnitOfWork()
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        cu = CreateClient(account_name, email, password)
        mb = MessageBus()
        mb.handle(cu, uow)
        uow.commited = False
        with pytest.raises(NotAvailableError):
            mb.handle(cu, uow)
        assert not uow.commited

    def test_create_service(self):
        uow = FakeUnitOfWork()
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["warsaw", "mechanic"]
        cu = CreateService(account_name, email, password, tags)
        mb = MessageBus()
        mb.handle(cu, uow)
        assert uow.commited
        user_stored = uow.users.list().pop().to_dict()
        assert user_stored["account_name"] == account_name
        assert user_stored["email"] == email
        assert user_stored["password"] == password
        assert user_stored["tags"] == tags
        calendar_stored = uow.calendars.list().pop()
        assert calendar_stored.owner == account_name

    def test_cannot_create_user_with_existing_account_name(self):
        uow = FakeUnitOfWork()
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["warsaw", "mechanic"]
        cu = CreateService(account_name, email, password, tags)
        mb = MessageBus()
        mb.handle(cu, uow)
        uow.commited = False
        with pytest.raises(NotAvailableError):
            mb.handle(cu, uow)
        assert not uow.commited


class TestCreateAppointment:
    def test_create_appoinment_when_free(self):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]

        mb = MessageBus()
        uow = FakeUnitOfWork()
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"

        uow.commited = False
        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)

        calendar_stored = uow.calendars.list().pop()
        [app_stored] = calendar_stored.list_appointments()
        app_stored = app_stored.to_dict()
        assert app_stored["from_user"] == from_user
        assert app_stored["since"] == since
        assert app_stored["until"] == until
        assert app_stored["description"] == description
        assert not app_stored["accepted"]
        assert uow.commited

    def test_create_appoinment_cannot_create_when_occupied(self):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]

        mb = MessageBus()
        uow = FakeUnitOfWork()
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)
        calendar_stored = uow.calendars.list()[0]
        [app_unaccepted] = calendar_stored.list_appointments()
        app_unaccepted = app_unaccepted.to_dict()
        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        mb.handle(ap, uow)

        from_user = "bob"
        since = datetime(2000, 1, 1, 1, 30)
        until = datetime(2000, 1, 1, 2)
        description = "car mechanic needed"

        uow.commited = False
        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        with pytest.raises(NotAvailableError):
            mb.handle(ca, uow)
        assert not uow.commited


class TestAcceptAppointment:
    def test_accept_appointment_when_free(self):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]

        mb = MessageBus()
        uow = FakeUnitOfWork()
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)
        calendar_stored = uow.calendars.list()[0]
        [app_unaccepted] = calendar_stored.list_appointments()
        app_unaccepted = app_unaccepted.to_dict()

        uow.commited = False
        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        mb.handle(ap, uow)
        [app_accepted] = calendar_stored.list_appointments()
        app_accepted = app_accepted.to_dict()

        assert app_accepted["from_user"] == from_user
        assert app_accepted["since"] == since
        assert app_accepted["until"] == until
        assert app_accepted["description"] == description
        assert app_accepted["accepted"]
        assert uow.commited

    def test_cannot_accept_when_occupied(self):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]

        mb = MessageBus()
        uow = FakeUnitOfWork()
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)
        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)

        from_user = "bob"
        since = datetime(2000, 1, 1, 1, 30)
        until = datetime(2000, 1, 1, 2)
        description = "car mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)
        calendar_stored = uow.calendars.list()[0]
        [
            app_unaccepted1,
            app_unaccepted2,
        ] = calendar_stored.list_appointments()
        app_unaccepted1 = app_unaccepted1.to_dict()
        app_unaccepted2 = app_unaccepted2.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        mb.handle(ap, uow)
        uow.commited = False
        ap = AcceptAppointment(to_user, app_unaccepted2["id"])
        with pytest.raises(DoesNotExistsError):
            mb.handle(ap, uow)
        assert not uow.commited

    def test_accept_when_wrong_id(self):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]

        mb = MessageBus()
        uow = FakeUnitOfWork()
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)
        calendar_stored = uow.calendars.list()[0]
        [app_unaccepted] = calendar_stored.list_appointments()
        app_unaccepted = app_unaccepted.to_dict()

        wrong_id = randint(1, 10)
        while wrong_id == app_unaccepted["id"]:
            wrong_id = randint(1, 10)

        uow.commited = False
        with pytest.raises(DoesNotExistsError):
            ap = AcceptAppointment(to_user, wrong_id)
            mb.handle(ap, uow)
        assert not uow.commited
