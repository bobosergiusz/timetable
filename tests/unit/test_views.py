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
from timetable.service_layer.views import (
    get_user,
    list_appointments,
    search_services,
    get_appointment,
)
from timetable.domain.exceptions import DoesNotExistsError


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
        u = get_user(account_name, uow)
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
        with pytest.raises(DoesNotExistsError):
            get_user("john", uow)
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
        mb.handle(ca, uow)

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

        calendar_stored = uow.calendars.list()[0]
        [app_obj1, app_obj2] = calendar_stored.list_appointments()
        app_unaccepted1 = app_obj1.to_dict()
        app_unaccepted2 = app_obj2.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        mb.handle(ap, uow)
        app_accepted1 = app_obj1.to_dict()

        uow.commited = False

        [app1_returned, app2_returned] = list_appointments(
            to_user, to_user, uow
        )

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
        mb.handle(ca, uow)

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

        calendar_stored = uow.calendars.list()[0]
        [app_obj1, app_obj2] = calendar_stored.list_appointments()
        app_unaccepted1 = app_obj1.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        mb.handle(ap, uow)

        app_accepted1 = app_obj1.to_dict()
        app_masked1 = dict()
        app_masked1["since"] = app_accepted1["since"]
        app_masked1["until"] = app_accepted1["until"]

        uow.commited = False
        [app1_returned] = list_appointments(to_user, from_user, uow)

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
        tags = tags_searched + ["lodz"]
        cu = CreateService(
            to_user3,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        [u1, _, u3] = uow.users.list()
        u1 = u1.to_dict()
        u3 = u3.to_dict()

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
        u_masked2["account_name"] = u3["account_name"]
        u_masked2["tags"] = u3["tags"]

        uow.commited = False
        found = search_services(tags_searched, uow)

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
        tags = tags + ["lodz"]
        cu = CreateService(
            to_user3,
            email,
            password,
            tags,
        )
        mb.handle(cu, uow)

        [u1, u2, u3] = uow.users.list()
        u1 = u1.to_dict()
        u2 = u2.to_dict()
        u3 = u3.to_dict()

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
        found = search_services([], uow)

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
        found = search_services(tags_searched, uow)

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
        mb.handle(ca, uow)

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

        calendar_stored = uow.calendars.list()[0]
        [app_obj, _] = calendar_stored.list_appointments()
        app_unaccepted = app_obj.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        mb.handle(ap, uow)
        app_accepted = app_obj.to_dict()

        uow.commited = False
        app_returned = get_appointment(to_user, app_accepted["id"], uow)

        assert app_returned == app_accepted
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
        mb.handle(ca, uow)

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
        calendar_stored = uow.calendars.list()[0]
        [app_obj, _] = calendar_stored.list_appointments()
        app_unaccepted = app_obj.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        mb.handle(ap, uow)
        app_accepted = app_obj.to_dict()

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
        with pytest.raises(DoesNotExistsError):
            get_appointment(wrong_service_name, app_accepted["id"], uow)

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
        mb.handle(ca, uow)

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
        calendar_stored = uow.calendars.list()[0]
        [app_obj1, app_obj2] = calendar_stored.list_appointments()
        app_unaccepted1 = app_obj1.to_dict()
        app_unaccepted2 = app_obj2.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        mb.handle(ap, uow)
        app_accepted1 = app_obj1.to_dict()

        uow.commited = False
        wrong_id = randint(1, 10)
        while (wrong_id == app_accepted1["id"]) or (
            wrong_id == app_unaccepted2["id"]
        ):
            wrong_id = randint(1, 10)
        with pytest.raises(DoesNotExistsError):
            get_appointment(to_user, wrong_id, uow)
        assert not uow.commited
