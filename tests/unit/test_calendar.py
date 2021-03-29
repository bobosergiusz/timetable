from datetime import datetime, timedelta
from random import randint

import pytest

from timetable.domain.calendar import Calendar
from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError


def test_can_create_appointment_when_free_and_time_valid():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    assert a.from_user == from_user
    assert a.since == since
    assert a.until == until
    assert a.description == description
    assert not a.accepted
    assert cal.list_appointments() == [a]


def test_cannot_create_appointment_when_until_higher_than_since():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = since + timedelta(hours=-1)
    description = "need doctor"

    with pytest.raises(ValueError):
        cal.create_appointment(
            from_user=from_user,
            since=since,
            until=until,
            description=description,
        )


def test_cannot_create_appointment_when_until_equal_to_since():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = since
    description = "need doctor"

    with pytest.raises(ValueError):
        cal.create_appointment(
            from_user=from_user,
            since=since,
            until=until,
            description=description,
        )


def test_can_create_appointment_next_to_other():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a1 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    from_user = "bob"
    since = datetime(2021, 1, 1, 12, 0, 0)
    until = datetime(2021, 1, 1, 13, 0, 0)
    description = "need car repair"

    a2 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    assert a2.from_user == from_user
    assert a2.since == since
    assert a2.until == until
    assert a2.description == description
    assert not a2.accepted
    assert cal.list_appointments() == [a1, a2]


def test_can_create_appointment_on_top_of_not_accepted():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a1 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    a2 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    assert a2.from_user == from_user
    assert a2.since == since
    assert a2.until == until
    assert a2.description == description
    assert not a2.accepted
    assert cal.list_appointments() == [a1, a2]


def test_can_accept_appointment():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    a = cal.accept_appointment(a)
    assert a.from_user == from_user
    assert a.since == since
    assert a.until == until
    assert a.description == description
    assert a.accepted


def test_cannot_create_appointment_when_collide_with_accepted():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    a = cal.accept_appointment(a)

    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"
    with pytest.raises(NotAvailableError):
        cal.create_appointment(
            from_user=from_user,
            since=since,
            until=until,
            description=description,
        )


def test_cannot_accept_appointment_when_collide_with_accepted():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a1 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    a2 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    a1 = cal.accept_appointment(a1)
    with pytest.raises(NotAvailableError):
        cal.accept_appointment(a2)


def test_accept_appointment_deletes_colliding():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    a = cal.accept_appointment(a)
    assert cal.list_appointments() == [a]


def test_cannot_accept_appointment_not_created():
    cal1 = Calendar(owner="katie")

    cal2 = Calendar(owner="elizabeth")
    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    a = cal2.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    with pytest.raises(DoesNotExistsError):
        cal1.accept_appointment(a)


def test_can_get_appointment_by_existing_id():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    a_retrieved = cal.get_appointment(a.id)
    assert a_retrieved == a


def test_cannot_get_appointment_by_unexisting_id():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a1 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    a2 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    id_unexisting = randint(3, 10)
    while (id_unexisting == a1.id) or (id_unexisting == a2.id):
        id_unexisting = randint(3, 10)

    with pytest.raises(DoesNotExistsError):
        cal.get_appointment(id_unexisting)


def test_can_list_appoitnments():
    cal = Calendar(owner="katie")

    from_user = "john"
    since = datetime(2020, 1, 1, 12, 0, 0)
    until = datetime(2020, 1, 1, 13, 0, 0)
    description = "need doctor"

    a1 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )
    from_user = "bob"
    since = datetime(2020, 1, 1, 12, 30, 0)
    until = datetime(2020, 1, 1, 13, 30, 0)
    description = "need car repair"

    a2 = cal.create_appointment(
        from_user=from_user, since=since, until=until, description=description
    )

    assert cal.list_appointments() == [a1, a2]
