from datetime import datetime

import pytest

from timetable.adapters.repository import SqlTrackingCalendarRepository
from timetable.domain.calendar import Calendar
from timetable.domain.exceptions import DoesNotExistsError

from tests.utils import insert_appointment, insert_calendar


def test_repository_can_add(Session):
    session = Session()
    owner = "bob"
    c = Calendar(owner=owner)
    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "need mechanic"
    a = c.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    repository = SqlTrackingCalendarRepository(session)
    repository.add(c)
    session.commit()

    [[owner_retrieved]] = session.execute("SELECT owner FROM calendars")

    [
        [
            calendar_owner_retrieved,
            id_appointment_retrieved,
            from_user_retrieved,
            since_retrieved,
            until_retrieved,
            description_retrieved,
            accepted_retrieved,
        ]
    ] = session.execute(
        "SELECT calendar_owner, id, from_user, since, "
        "until,description, accepted "
        "FROM appointments"
    )

    assert owner_retrieved == owner
    assert calendar_owner_retrieved == owner
    assert id_appointment_retrieved == a.id
    assert from_user_retrieved == from_user
    assert since_retrieved == a.since.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert until_retrieved == a.until.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert description_retrieved == description_retrieved
    assert accepted_retrieved == a.accepted
    assert repository.seen == {c}


def test_repository_can_get_by_existing_id(Session):
    session = Session()
    owner = "bob"
    insert_calendar(session, owner)

    [[owner]] = session.execute("SELECT owner FROM calendars")
    from_user = "john"
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    description = "mechanic needed"
    accepted = True
    insert_appointment(
        session,
        owner,
        from_user,
        since,
        until,
        description,
        accepted,
    )
    repository = SqlTrackingCalendarRepository(session)
    c = repository.get(owner)

    assert c.owner == owner

    [a] = c.list_appointments()
    assert a.from_user == from_user
    assert a.since == since
    assert a.until == until
    assert a.description == description
    assert a.accepted
    assert repository.seen == {c}


def test_repository_cannot_get_by_nonexisting_id(Session):
    session = Session()
    repository = SqlTrackingCalendarRepository(session)
    with pytest.raises(DoesNotExistsError):
        repository.get(3)


def test_repository_can_list(Session):
    session = Session()
    owner1 = "bob"
    insert_calendar(session, owner1)
    owner2 = "elizabeth"
    insert_calendar(session, owner2)

    [[owner1], [owner2]] = session.execute("SELECT owner FROM calendars")
    from_user11 = "john"
    since11 = datetime(2000, 1, 1, 1)
    until11 = datetime(2000, 1, 1, 2)
    description11 = "mechanic needed"
    accepted11 = True
    insert_appointment(
        session,
        owner1,
        from_user11,
        since11,
        until11,
        description11,
        accepted11,
    )
    from_user12 = "katie"
    since12 = datetime(2000, 1, 2, 1)
    until12 = datetime(2000, 1, 3, 2)
    description12 = "car repair"
    accepted12 = True
    insert_appointment(
        session,
        owner1,
        from_user12,
        since12,
        until12,
        description12,
        accepted12,
    )
    from_user21 = "john"
    since21 = datetime(2000, 1, 1, 1)
    until21 = datetime(2000, 1, 1, 2)
    description21 = "sore throat"
    accepted21 = False
    insert_appointment(
        session,
        owner2,
        from_user21,
        since21,
        until21,
        description21,
        accepted21,
    )

    repository = SqlTrackingCalendarRepository(session)
    [c1, c2] = repository.list()

    assert c1.owner == owner1
    assert c2.owner == owner2
    assert repository.seen == {c1, c2}

    [a11, a12] = c1.list_appointments()
    [a21] = c2.list_appointments()

    assert a11.from_user == from_user11
    assert a11.since == since11
    assert a11.until == until11
    assert a11.description == description11
    assert a11.accepted
    assert a12.from_user == from_user12
    assert a12.since == since12
    assert a12.until == until12
    assert a12.description == description12
    assert a12.accepted
    assert a21.from_user == from_user21
    assert a21.since == since21
    assert a21.until == until21
    assert a21.description == description21
    assert not a21.accepted
