from datetime import datetime
from random import randint

import pytest
from tests.fakes import FakeUnitOfWork

from timetable.domain.command import (
    CreateClient,
    CreateService,
    CreateAppointment,
    AcceptAppointment,
    GetUser,
    GetAppointment,
    ListAppointments,
    SearchServices,
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
        [u] = mb.handle(cu, uow)
        assert u["account_name"] == account_name
        assert u["email"] == email
        assert u["password"] == password
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
        [u] = mb.handle(cu, uow)
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


class TestGetUser:
    def test_get_existing_user(self):
        uow = FakeUnitOfWork()
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["warsaw", "mechanic"]
        cu = CreateService(account_name, email, password, tags)
        mb = MessageBus()
        mb.handle(cu, uow)
        uow.commited = False
        gu = GetUser(account_name)
        [u] = mb.handle(gu, uow)
        assert u["account_name"] == account_name
        assert u["email"] == email
        assert u["password"] == password
        assert u["tags"] == tags
        assert not uow.commited

    def test_cannot_get_unexisting_user(self):
        uow = FakeUnitOfWork()
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["warsaw", "mechanic"]
        cu = CreateService(account_name, email, password, tags)
        mb = MessageBus()
        mb.handle(cu, uow)
        uow.commited = False
        gu = GetUser("john")
        with pytest.raises(DoesNotExistsError):
            mb.handle(gu, uow)
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
        [app_returned] = mb.handle(ca, uow)

        calendar_stored = uow.calendars.list().pop()
        app_stored = calendar_stored.get_appointment(
            app_returned["id"]
        ).to_dict()
        assert app_returned["from_user"] == from_user
        assert app_returned["since"] == since
        assert app_returned["until"] == until
        assert app_returned["description"] == description
        assert not app_returned["accepted"]
        assert app_stored == app_returned
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
        [app_unaccepted] = mb.handle(ca, uow)
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
        [app_unaccepted] = mb.handle(ca, uow)

        uow.commited = False
        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        [app_returned] = mb.handle(ap, uow)

        calendar_stored = uow.calendars.list().pop()
        app_stored = calendar_stored.get_appointment(
            app_returned["id"]
        ).to_dict()
        assert app_returned["from_user"] == from_user
        assert app_returned["since"] == since
        assert app_returned["until"] == until
        assert app_returned["description"] == description
        assert app_returned["accepted"]
        assert app_stored == app_returned
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
        [app_unaccepted1] = mb.handle(ca, uow)

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
        [app_unaccepted2] = mb.handle(ca, uow)

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
        [app_unaccepted] = mb.handle(ca, uow)

        wrong_id = randint(1, 10)
        while wrong_id == app_unaccepted["id"]:
            wrong_id = randint(1, 10)

        uow.commited = False
        with pytest.raises(DoesNotExistsError):
            ap = AcceptAppointment(to_user, wrong_id)
            mb.handle(ap, uow)
        assert not uow.commited


class TestListAppointments:
    def test_list_appointments_owned(self):
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
        [app_unaccepted1] = mb.handle(ca, uow)

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        [app_unaccepted2] = mb.handle(ca, uow)

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        [app_accepted1] = mb.handle(ap, uow)

        uow.commited = False

        la = ListAppointments(to_user, to_user)
        [[app1_returned, app2_returned]] = mb.handle(la, uow)

        assert app_accepted1 == app1_returned
        assert app_unaccepted2 == app2_returned
        assert not uow.commited

    def test_list_appointments_unowned(self):
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
        [app_unaccepted1] = mb.handle(ca, uow)

        from_user = "katherine"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        [app_accepted1] = mb.handle(ap, uow)
        app_masked1 = dict()
        app_masked1["since"] = app_accepted1["since"]
        app_masked1["until"] = app_accepted1["until"]

        uow.commited = False
        la = ListAppointments(to_user, from_user)
        [[app1_returned]] = mb.handle(la, uow)

        assert app_masked1 == app1_returned
        assert not uow.commited


class TestSearchServices:
    def test_search_services_by_tag(self):
        tags_searched = ["mechanic", "warsaw"]

        mb = MessageBus()
        uow = FakeUnitOfWork()

        to_user1 = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = tags_searched + ["cars"]
        cu = CreateService(
            to_user1,
            email,
            password,
            tags,
        )
        [u1] = mb.handle(cu, uow)

        to_user2 = "james"
        email = "james@dot.com"
        password = "123"
        tags = ["doctor", "medicine"]
        cu = CreateService(
            to_user2,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        to_user3 = "katie"
        email = "katie@dot.com"
        password = "123"
        tags = tags_searched + ["lodz"]
        cu = CreateService(
            to_user3,
            email,
            password,
            tags,
        )
        [u2] = mb.handle(cu, uow)

        account_name = "john"
        email = "john@dot.com"
        password = "123"
        cu = CreateClient(
            account_name,
            email,
            password,
        )
        mb.handle(cu, uow)

        u_masked1 = dict()
        u_masked1["account_name"] = u1["account_name"]
        u_masked1["tags"] = u1["tags"]
        u_masked2 = dict()
        u_masked2["account_name"] = u2["account_name"]
        u_masked2["tags"] = u2["tags"]

        uow.commited = False
        ss = SearchServices(tags_searched)
        [found] = mb.handle(ss, uow)

        assert found == [u_masked1, u_masked2]
        assert not uow.commited

    def test_search_services_no_tag(self):
        tags = ["mechanic", "warsaw"]

        mb = MessageBus()
        uow = FakeUnitOfWork()

        to_user1 = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = tags + ["cars"]
        cu = CreateService(
            to_user1,
            email,
            password,
            tags,
        )
        [u1] = mb.handle(cu, uow)

        to_user2 = "james"
        email = "james@dot.com"
        password = "123"
        tags = ["doctor", "medicine"]
        cu = CreateService(
            to_user2,
            email,
            password,
            tags,
        )
        [u2] = mb.handle(cu, uow)

        to_user3 = "katie"
        email = "katie@dot.com"
        password = "123"
        tags = tags + ["lodz"]
        cu = CreateService(
            to_user3,
            email,
            password,
            tags,
        )
        [u3] = mb.handle(cu, uow)

        account_name = "john"
        email = "john@dot.com"
        password = "123"
        cu = CreateClient(
            account_name,
            email,
            password,
        )
        mb.handle(cu, uow)

        u_masked1 = dict()
        u_masked1["account_name"] = u1["account_name"]
        u_masked1["tags"] = u1["tags"]
        u_masked2 = dict()
        u_masked2["account_name"] = u2["account_name"]
        u_masked2["tags"] = u2["tags"]
        u_masked3 = dict()
        u_masked3["account_name"] = u3["account_name"]
        u_masked3["tags"] = u3["tags"]

        uow.commited = False
        ss = SearchServices([])
        [found] = mb.handle(ss, uow)

        assert found == [u_masked1, u_masked2, u_masked3]
        assert not uow.commited

    def test_search_services_by_tag_empty(self):
        tags_searched = ["mechanic", "warsaw"]

        mb = MessageBus()
        uow = FakeUnitOfWork()

        to_user1 = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["cars"]
        cu = CreateService(
            to_user1,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        to_user2 = "james"
        email = "james@dot.com"
        password = "123"
        tags = ["doctor", "medicine"]
        cu = CreateService(
            to_user2,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        to_user3 = "katie"
        email = "katie@dot.com"
        password = "123"
        tags = ["tags"]
        cu = CreateService(
            to_user3,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        account_name = "john"
        email = "john@dot.com"
        password = "123"
        cu = CreateClient(account_name, email, password)
        mb.handle(cu, uow)

        uow.commited = False
        tags_searched = ["mechanic", "warsaw"]
        ss = SearchServices(tags_searched)
        [found] = mb.handle(ss, uow)

        assert found == []
        assert not uow.commited


class TestGetAppointmentDetail:
    def test_get_appointment_detail_existing(self):
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
        [app_unaccepted1] = mb.handle(ca, uow)

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        [app_accepted1] = mb.handle(ap, uow)

        uow.commited = False
        ga = GetAppointment(to_user, app_accepted1["id"])
        [app_returned] = mb.handle(ga, uow)

        assert app_returned == app_accepted1
        assert not uow.commited

    def test_get_appointment_detail_unexisting_service(self):
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
        [app_unaccepted1] = mb.handle(ca, uow)

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        mb.handle(ca, uow)

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        [app_accepted1] = mb.handle(ap, uow)

        wrong_service_name = "dylan"
        email = "dylan@dot.com"
        password = "123"
        cu = CreateClient(
            wrong_service_name,
            email,
            password,
        )
        mb.handle(cu, uow)

        uow.commited = False
        ga = GetAppointment(wrong_service_name, app_accepted1["id"])
        with pytest.raises(DoesNotExistsError):
            mb.handle(ga, uow)

        assert not uow.commited

    def test_get_appointment_detail_unexisting_app_id(self):
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
        [app_unaccepted1] = mb.handle(ca, uow)

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"

        ca = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        [app_unaccepted] = mb.handle(ca, uow)

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        [app_accepted] = mb.handle(ap, uow)

        uow.commited = False
        wrong_id = randint(1, 10)
        while (wrong_id == app_accepted["id"]) or (
            wrong_id == app_unaccepted["id"]
        ):
            wrong_id = randint(1, 10)
        ga = GetAppointment(to_user, wrong_id)
        with pytest.raises(DoesNotExistsError):
            mb.handle(ga, uow)
        assert not uow.commited
