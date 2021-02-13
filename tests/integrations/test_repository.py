from datetime import datetime

import pytest

from timetable.adapters.repository import DoesNotExistsError, SqlRepository
from timetable.domain.appointment import Appointment


def test_repository_can_add(Session):
    session = Session()
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    a = Appointment(since=since, until=until, accepted=False)

    repository = SqlRepository(session)
    repository.add(a)
    session.commit()

    [[since_retrieved, until_retrieved, accepted_retrieved]] = session.execute(
        "SELECT since, until, accepted FROM appointments"
    )

    assert since_retrieved == a.since.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert until_retrieved == a.until.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert accepted_retrieved == a.accepted


def insert(session, since: datetime, until: datetime, accepted: bool) -> None:
    session.execute(
        "INSERT INTO appointments (since, until, accepted) "
        "VALUES (:since, :until, :accepted)",
        {"since": since, "until": until, "accepted": accepted},
    )


def test_repository_can_get_by_existing_id(Session):
    session = Session()
    since = datetime(2000, 1, 1, 1)
    until = datetime(2000, 1, 1, 2)
    insert(session, since, until, True)
    [[id_]] = session.execute("SELECT id FROM appointments")
    repository = SqlRepository(session)
    a = repository.get(id_)

    assert a.since == since
    assert a.until == until
    assert a.accepted


def test_repository_cannot_get_by_nonexisting_id(Session):
    session = Session()
    repository = SqlRepository(session)
    with pytest.raises(DoesNotExistsError):
        repository.get(3)


def test_repository_can_list(Session):
    session = Session()
    since1 = datetime(2000, 1, 1, 1)
    until1 = datetime(2000, 1, 1, 2)
    insert(session, since1, until1, True)
    since2 = datetime(2000, 1, 2, 1)
    until2 = datetime(2000, 1, 2, 2)
    insert(session, since2, until2, False)
    [[id1], [id2]] = session.execute("SELECT id FROM appointments")
    repository = SqlRepository(session)
    a1 = repository.get(id1)
    a2 = repository.get(id2)

    assert a1.since == since1
    assert a1.until == until1
    assert a1.accepted

    assert a2.since == since2
    assert a2.until == until2
    assert not a2.accepted
