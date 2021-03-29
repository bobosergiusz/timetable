from datetime import datetime
from typing import List
from random import randint

import pytest

from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError
from timetable.domain.user import User, Service
from timetable.domain.calendar import Calendar
from timetable.service_layer.services import (
    accept_appointment,
    create_appointment,
    list_appointments_owned,
    list_appointments_unowned,
    create_client,
    create_service,
    get_user,
    search_services,
    get_appointment,
)


class FakeCalendarRepository:
    def __init__(self, cals: List[Calendar]):
        self.cals = cals

    def get(self, owner: str) -> Calendar:
        cal = next((a for a in self.cals if a.owner == owner), None)
        if cal is None:
            raise DoesNotExistsError
        return cal

    def list(self) -> List[Calendar]:
        return self.cals

    def add(self, cal: Calendar):
        owner = cal.owner
        i = next(
            (i for i, a in enumerate(self.cals) if a.owner == owner), None
        )
        if i is None:
            self.cals.append(cal)
        else:
            self.cals[i] = cal


class FakeUsersRepository:
    def __init__(self, users: List[User]):
        self.users = users

    def get(self, account_name: str) -> User:
        user = next(
            (u for u in self.users if u.account_name == account_name), None
        )
        if user is None:
            raise DoesNotExistsError
        return user

    def list(self) -> List[User]:
        return self.users

    def list_services(self) -> List[Service]:
        filtered = [u for u in self.users if isinstance(u, Service)]
        return filtered

    def add(self, user: User):
        user_saved = next(
            (u for u in self.users if u.account_name == id), None
        )
        if user_saved is not None:
            self.users.remove(user_saved)
        self.users.append(user)


class FakeUnitOfWork:
    def __init__(self):
        self.commited = False
        self.calendars = FakeCalendarRepository([])
        self.users = FakeUsersRepository([])

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def rollback(self):
        pass

    def commit(self):
        self.commited = True


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
    calendar_stored = uow.calendars.list().pop()
    assert calendar_stored.owner == account_name


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


def test_create_appoinment_when_free():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    uow.commited = False
    app_returned = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    calendar_stored = uow.calendars.list().pop()
    app_stored = calendar_stored.get_appointment(app_returned["id"]).to_dict()
    assert app_returned["from_user"] == from_user
    assert app_returned["since"] == since
    assert app_returned["until"] == until
    assert app_returned["description"] == description
    assert not app_returned["accepted"]
    assert app_stored == app_returned
    assert uow.commited


def test_accept_appointment_when_free():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    uow.commited = False
    app_returned = accept_appointment(to_user, app_unaccepted["id"], uow)

    calendar_stored = uow.calendars.list().pop()
    app_stored = calendar_stored.get_appointment(app_returned["id"]).to_dict()
    assert app_returned["from_user"] == from_user
    assert app_returned["since"] == since
    assert app_returned["until"] == until
    assert app_returned["description"] == description
    assert app_returned["accepted"]
    assert app_stored == app_returned
    assert uow.commited


def test_ask_appoinment_cannot_create_when_occupied():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    accept_appointment(to_user, app_unaccepted["id"], uow)

    from_user = "bob"
    since = datetime(2000, 1, 1, 1, 30)
    until = datetime(2000, 1, 1, 2)
    description = "car mechanic needed"

    uow.commited = False
    with pytest.raises(NotAvailableError):
        create_appointment(to_user, from_user, since, until, description, uow)
    assert not uow.commited


def test_cannot_accept_when_occupied():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted1 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    from_user = "bob"
    since = datetime(2000, 1, 1, 1, 30)
    until = datetime(2000, 1, 1, 2)
    description = "car mechanic needed"

    app_unaccepted2 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    accept_appointment(to_user, app_unaccepted1["id"], uow)
    uow.commited = False
    with pytest.raises(DoesNotExistsError):
        accept_appointment(to_user, app_unaccepted2["id"], uow)
    assert not uow.commited


def test_accept_when_wrong_id():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    uow.commited = False
    wrong_id = randint(1, 10)
    while wrong_id == app_unaccepted["id"]:
        wrong_id = randint(1, 10)

    uow.commited = False
    with pytest.raises(DoesNotExistsError):
        accept_appointment(to_user, wrong_id, uow)
    assert not uow.commited


def test_list_appointments_owned():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted1 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    from_user = "bob"
    since = datetime(2000, 1, 1, 3, 30)
    until = datetime(2000, 1, 1, 4)
    description = "car mechanic needed"

    app_unaccepted2 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    app_accepted1 = accept_appointment(to_user, app_unaccepted1["id"], uow)

    uow.commited = False
    [app1_returned, app2_returned] = list_appointments_owned(to_user, uow)

    assert app_accepted1 == app1_returned
    assert app_unaccepted2 == app2_returned
    assert not uow.commited


def test_list_appointments_unowned():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted1 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    from_user = "bob"
    since = datetime(2000, 1, 1, 3, 30)
    until = datetime(2000, 1, 1, 4)
    description = "car mechanic needed"

    app_unaccepted2 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    app_accepted1 = accept_appointment(to_user, app_unaccepted1["id"], uow)
    app_masked1 = dict()
    app_masked1["since"] = app_accepted1["since"]
    app_masked1["until"] = app_accepted1["until"]
    app_masked2 = dict()
    app_masked2["since"] = app_unaccepted2["since"]
    app_masked2["until"] = app_unaccepted2["until"]

    uow.commited = False
    [app1_returned, app2_returned] = list_appointments_unowned(to_user, uow)

    assert app_masked1 == app1_returned
    assert app_masked2 == app2_returned
    assert not uow.commited


def test_search_services_by_tag():
    tags_searched = ["mechanic", "warsaw"]
    uow = FakeUnitOfWork()
    to_user1 = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = tags_searched + ["cars"]
    u1 = create_service(to_user1, email, password, tags, uow)
    to_user2 = "james"
    email = "james@dot.com"
    password = "123"
    tags = ["doctor", "medicine"]
    create_service(to_user2, email, password, tags, uow)
    to_user3 = "katie"
    email = "katie@dot.com"
    password = "123"
    tags = tags_searched + ["lodz"]
    u2 = create_service(to_user3, email, password, tags, uow)
    account_name = "john"
    email = "john@dot.com"
    password = "123"
    create_client(account_name, email, password, uow)

    u_masked1 = dict()
    u_masked1["account_name"] = u1["account_name"]
    u_masked1["tags"] = u1["tags"]
    u_masked2 = dict()
    u_masked2["account_name"] = u2["account_name"]
    u_masked2["tags"] = u2["tags"]

    uow.commited = False
    found = search_services(tags_searched, uow)

    assert found == [u_masked1, u_masked2]
    assert not uow.commited


def test_search_services_no_tag():
    tags = ["mechanic", "warsaw"]
    uow = FakeUnitOfWork()
    to_user1 = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = tags + ["cars"]
    u1 = create_service(to_user1, email, password, tags, uow)
    to_user2 = "james"
    email = "james@dot.com"
    password = "123"
    tags = ["doctor", "medicine"]
    u2 = create_service(to_user2, email, password, tags, uow)
    to_user3 = "katie"
    email = "katie@dot.com"
    password = "123"
    tags = tags + ["lodz"]
    u3 = create_service(to_user3, email, password, tags, uow)
    account_name = "john"
    email = "john@dot.com"
    password = "123"
    create_client(account_name, email, password, uow)

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


def test_search_services_by_tag_empty():
    tags_searched = ["mechanic", "warsaw"]
    uow = FakeUnitOfWork()
    to_user1 = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["cars"]
    create_service(to_user1, email, password, tags, uow)
    to_user2 = "james"
    email = "james@dot.com"
    password = "123"
    tags = ["doctor", "medicine"]
    create_service(to_user2, email, password, tags, uow)
    to_user3 = "katie"
    email = "katie@dot.com"
    password = "123"
    tags = ["tags"]
    create_service(to_user3, email, password, tags, uow)
    account_name = "john"
    email = "john@dot.com"
    password = "123"
    create_client(account_name, email, password, uow)
    uow.commited = False
    tags_searched = ["mechanic", "warsaw"]
    found = search_services(tags_searched, uow)

    assert found == []
    assert not uow.commited


def test_get_appointment_detail_existing():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted1 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    from_user = "bob"
    since = datetime(2000, 1, 1, 3, 30)
    until = datetime(2000, 1, 1, 4)
    description = "car mechanic needed"

    create_appointment(to_user, from_user, since, until, description, uow)

    app_accepted1 = accept_appointment(to_user, app_unaccepted1["id"], uow)

    uow.commited = False
    app_returned = get_appointment(to_user, app_accepted1["id"], uow)

    assert app_returned == app_accepted1
    assert not uow.commited


def test_get_appointment_detail_unexisting_service():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted1 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    from_user = "bob"
    since = datetime(2000, 1, 1, 3, 30)
    until = datetime(2000, 1, 1, 4)
    description = "car mechanic needed"

    create_appointment(to_user, from_user, since, until, description, uow)

    app_accepted1 = accept_appointment(to_user, app_unaccepted1["id"], uow)
    wrong_service_name = "dylan"
    email = "dylan@dot.com"
    password = "123"
    create_client(wrong_service_name, email, password, uow)

    uow.commited = False
    with pytest.raises(DoesNotExistsError):
        get_appointment(wrong_service_name, app_accepted1["id"], uow)

    assert not uow.commited


def test_get_appointment_detail_unexisting_app_id():
    to_user = "bob"
    email = "bob@dot.com"
    password = "123"
    tags = ["mechanic", "car"]

    uow = FakeUnitOfWork()
    create_service(to_user, email, password, tags, uow)

    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"

    app_unaccepted1 = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    from_user = "bob"
    since = datetime(2000, 1, 1, 3, 30)
    until = datetime(2000, 1, 1, 4)
    description = "car mechanic needed"

    app_unaccepted = create_appointment(
        to_user, from_user, since, until, description, uow
    )

    app_accepted = accept_appointment(to_user, app_unaccepted1["id"], uow)

    uow.commited = False
    wrong_id = randint(1, 10)
    while (wrong_id == app_accepted["id"]) or (
        wrong_id == app_unaccepted["id"]
    ):
        wrong_id = randint(1, 10)
    with pytest.raises(DoesNotExistsError):
        get_appointment(to_user, wrong_id, uow)

    assert not uow.commited
