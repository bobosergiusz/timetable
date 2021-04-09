from datetime import datetime
from random import randint

import pytest

from timetable.domain.command import (
    CreateClient,
    CreateService,
    CreateAppointment,
    AcceptAppointment,
)
from timetable.service_layer.views import (
    get_user,
    list_appointments,
    search_services,
    get_appointment,
)
from timetable.domain.exceptions import DoesNotExistsError


class TestGetUser:
    def test_get_existing_user(self, fake_mb):
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["warsaw", "mechanic"]
        cu = CreateService(account_name, email, password, tags)

        fake_mb.handle(cu)

        u = get_user(account_name, fake_mb.uow)

        assert u["account_name"] == account_name
        assert u["email"] == email
        assert u["password"] == password
        assert u["tags"] == tags

    def test_cannot_get_unexisting_user(self, fake_mb):
        account_name = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["warsaw", "mechanic"]
        cu = CreateService(account_name, email, password, tags)

        fake_mb.handle(cu)

        with pytest.raises(DoesNotExistsError):
            get_user("john", fake_mb.uow)


class TestListAppointments:
    def test_list_appointments_owned(self, fake_mb):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"
        ca1 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        model1 = {
            "from_user": from_user,
            "since": since,
            "until": until,
            "description": description,
            "accepted": True,
        }

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"
        ca2 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        model2 = {
            "from_user": from_user,
            "since": since,
            "until": until,
            "description": description,
            "accepted": False,
        }

        fake_mb.handle(cu)
        fake_mb.handle(ca1)
        fake_mb.handle(ca2)

        calendar_stored = fake_mb.uow.calendars.list()[0]
        [app_obj1_unaccepted, _] = calendar_stored.list_appointments()
        app_unaccepted1 = app_obj1_unaccepted.to_dict()
        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        fake_mb.handle(ap)

        [app1_returned, app2_returned] = list_appointments(
            to_user, to_user, fake_mb.uow
        )
        del app1_returned["id"]
        del app2_returned["id"]

        assert app1_returned == model1
        assert app2_returned == model2

    def test_list_appointments_unowned(self, fake_mb):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"
        model = {
            "since": since,
            "until": until,
        }
        ca1 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        from_user = "katherine"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"
        ca2 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        fake_mb.handle(cu)
        fake_mb.handle(ca1)
        fake_mb.handle(ca2)

        calendar_stored = fake_mb.uow.calendars.list()[0]
        [app_obj1, _] = calendar_stored.list_appointments()
        app_unaccepted1 = app_obj1.to_dict()

        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        fake_mb.handle(ap)

        [app1_returned] = list_appointments(to_user, from_user, fake_mb.uow)

        assert app1_returned == model


class TestSearchServices:
    def test_search_services_by_tag(self, fake_mb):
        tags_searched = ["mechanic", "warsaw"]

        to_user1 = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = tags_searched + ["cars"]
        cu1 = CreateService(
            to_user1,
            email,
            password,
            tags,
        )

        to_user2 = "james"
        email = "james@dot.com"
        password = "123"
        tags = ["doctor", "medicine"]
        cu2 = CreateService(
            to_user2,
            email,
            password,
            tags,
        )

        to_user3 = "katie"
        email = "katie@dot.com"
        password = "123"
        tags = tags_searched + ["lodz"]
        cu3 = CreateService(
            to_user3,
            email,
            password,
            tags,
        )

        account_name = "john"
        email = "john@dot.com"
        password = "123"
        cu4 = CreateClient(
            account_name,
            email,
            password,
        )

        fake_mb.handle(cu1)
        fake_mb.handle(cu2)
        fake_mb.handle(cu3)
        fake_mb.handle(cu4)

        [u1, _, u3, _] = fake_mb.uow.users.list()
        u1 = u1.to_dict()
        u3 = u3.to_dict()
        u_masked1 = dict()
        u_masked1["account_name"] = u1["account_name"]
        u_masked1["tags"] = u1["tags"]
        u_masked2 = dict()
        u_masked2["account_name"] = u3["account_name"]
        u_masked2["tags"] = u3["tags"]

        found = search_services(tags_searched, fake_mb.uow)

        assert found == [u_masked1, u_masked2]

    def test_search_services_no_tag(self, fake_mb):
        tags = ["mechanic", "warsaw"]

        to_user1 = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = tags + ["cars"]
        cu1 = CreateService(
            to_user1,
            email,
            password,
            tags,
        )

        to_user2 = "james"
        email = "james@dot.com"
        password = "123"
        tags = ["doctor", "medicine"]
        cu2 = CreateService(
            to_user2,
            email,
            password,
            tags,
        )

        to_user3 = "katie"
        email = "katie@dot.com"
        password = "123"
        tags = tags + ["lodz"]
        cu3 = CreateService(
            to_user3,
            email,
            password,
            tags,
        )

        account_name = "john"
        email = "john@dot.com"
        password = "123"
        cu4 = CreateClient(
            account_name,
            email,
            password,
        )

        fake_mb.handle(cu1)
        fake_mb.handle(cu2)
        fake_mb.handle(cu3)
        fake_mb.handle(cu4)

        [u1, u2, u3, _] = fake_mb.uow.users.list()
        u1 = u1.to_dict()
        u2 = u2.to_dict()
        u3 = u3.to_dict()
        u_masked1 = dict()
        u_masked1["account_name"] = u1["account_name"]
        u_masked1["tags"] = u1["tags"]
        u_masked2 = dict()
        u_masked2["account_name"] = u2["account_name"]
        u_masked2["tags"] = u2["tags"]
        u_masked3 = dict()
        u_masked3["account_name"] = u3["account_name"]
        u_masked3["tags"] = u3["tags"]

        found = search_services([], fake_mb.uow)

        assert found == [u_masked1, u_masked2, u_masked3]

    def test_search_services_by_tag_empty(self, fake_mb):
        tags_searched = ["mechanic", "warsaw"]

        to_user1 = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["cars"]
        cu1 = CreateService(
            to_user1,
            email,
            password,
            tags,
        )

        to_user2 = "james"
        email = "james@dot.com"
        password = "123"
        tags = ["doctor", "medicine"]
        cu2 = CreateService(
            to_user2,
            email,
            password,
            tags,
        )

        to_user3 = "katie"
        email = "katie@dot.com"
        password = "123"
        tags = ["tags"]
        cu3 = CreateService(
            to_user3,
            email,
            password,
            tags,
        )

        account_name = "john"
        email = "john@dot.com"
        password = "123"
        cu4 = CreateClient(account_name, email, password)

        fake_mb.handle(cu1)
        fake_mb.handle(cu2)
        fake_mb.handle(cu3)
        fake_mb.handle(cu4)

        tags_searched = ["mechanic", "warsaw"]
        found = search_services(tags_searched, fake_mb.uow)

        assert found == []


class TestGetAppointmentDetail:
    def test_get_appointment_detail_existing(self, fake_mb):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"
        ca1 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )
        model = {
            "from_user": from_user,
            "since": since,
            "until": until,
            "description": description,
            "accepted": True,
        }

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"
        ca2 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        fake_mb.handle(cu)
        fake_mb.handle(ca1)
        fake_mb.handle(ca2)

        calendar_stored = fake_mb.uow.calendars.list()[0]
        [app_obj_unaccepted, _] = calendar_stored.list_appointments()
        app_unaccepted = app_obj_unaccepted.to_dict()
        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        fake_mb.handle(ap)

        app_returned = get_appointment(
            to_user, app_unaccepted["id"], fake_mb.uow
        )
        del app_returned["id"]

        assert app_returned == model

    def test_get_appointment_detail_unexisting_service(self, fake_mb):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]
        cu1 = CreateService(
            to_user,
            email,
            password,
            tags,
        )

        wrong_service_name = "dylan"
        email = "dylan@dot.com"
        password = "123"
        cu2 = CreateClient(
            wrong_service_name,
            email,
            password,
        )

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"
        ca1 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"
        ca2 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        fake_mb.handle(cu1)
        fake_mb.handle(cu2)
        fake_mb.handle(ca1)
        fake_mb.handle(ca2)

        calendar_stored = fake_mb.uow.calendars.list()[0]
        [app_obj_unaccepted, _] = calendar_stored.list_appointments()
        app_unaccepted = app_obj_unaccepted.to_dict()
        ap = AcceptAppointment(to_user, app_unaccepted["id"])
        fake_mb.handle(ap)

        with pytest.raises(DoesNotExistsError):
            get_appointment(
                wrong_service_name, app_unaccepted["id"], fake_mb.uow
            )

    def test_get_appointment_detail_unexisting_app_id(self, fake_mb):
        to_user = "bob"
        email = "bob@dot.com"
        password = "123"
        tags = ["mechanic", "car"]
        cu = CreateService(
            to_user,
            email,
            password,
            tags,
        )

        from_user = "john"
        since = datetime(2000, 1, 1, 1)
        until = datetime(2000, 1, 1, 2)
        description = "mechanic needed"
        ca1 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        from_user = "bob"
        since = datetime(2000, 1, 1, 3, 30)
        until = datetime(2000, 1, 1, 4)
        description = "car mechanic needed"
        ca2 = CreateAppointment(
            to_user,
            from_user,
            since,
            until,
            description,
        )

        fake_mb.handle(cu)
        fake_mb.handle(ca1)
        fake_mb.handle(ca2)

        calendar_stored = fake_mb.uow.calendars.list()[0]
        [app_obj1, app_obj2] = calendar_stored.list_appointments()
        app_unaccepted1 = app_obj1.to_dict()
        app_unaccepted2 = app_obj2.to_dict()
        ap = AcceptAppointment(to_user, app_unaccepted1["id"])
        fake_mb.handle(ap)

        wrong_id = randint(1, 10)
        while (wrong_id == app_unaccepted1["id"]) or (
            wrong_id == app_unaccepted2["id"]
        ):
            wrong_id = randint(1, 10)
        with pytest.raises(DoesNotExistsError):
            get_appointment(to_user, wrong_id, fake_mb.uow)
