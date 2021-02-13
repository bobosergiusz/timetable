from datetime import datetime, timedelta

import pytest


from timetable.model.appointment import Appointment


def test_can_create_when_lower_limit_less_than_upper():
    lower = datetime(2020, 1, 1, 12, 0, 0)
    upper = lower + timedelta(hours=1)
    a = Appointment(since=lower, until=upper, accepted=False)
    assert a.since < a.until


def test_cannot_create_with_lower_limit_greater_than_upper():
    lower = datetime(2020, 1, 1, 12, 0, 0)
    upper = lower + timedelta(hours=-1)
    with pytest.raises(ValueError):
        _ = Appointment(since=lower, until=upper, accepted=False)


def test_cannot_create_with_lower_limit_equal_to_upper():
    lower = datetime(2020, 1, 1, 12, 0, 0)
    upper = lower
    with pytest.raises(ValueError):
        _ = Appointment(since=lower, until=upper, accepted=False)


def test_separate_not_collide():
    lower1 = datetime(2020, 1, 1, 12, 0, 0)
    upper1 = datetime(2020, 1, 1, 13, 0, 0)
    lower2 = datetime(2020, 1, 1, 14, 0, 0)
    upper2 = datetime(2020, 1, 1, 16, 0, 0)
    a1 = Appointment(since=lower1, until=upper1, accepted=False)
    a2 = Appointment(since=lower2, until=upper2, accepted=False)
    assert not a1.collide(a2)
    assert not a2.collide(a1)


def test_next_to_not_collide():
    lower1 = datetime(2020, 1, 1, 12, 0, 0)
    upper1 = datetime(2020, 1, 1, 13, 0, 0)
    lower2 = datetime(2020, 1, 1, 13, 0, 0)
    upper2 = datetime(2020, 1, 1, 16, 0, 0)
    a1 = Appointment(since=lower1, until=upper1, accepted=False)
    a2 = Appointment(since=lower2, until=upper2, accepted=False)
    assert not a1.collide(a2)
    assert not a2.collide(a1)


def test_collide():
    lower1 = datetime(2020, 1, 1, 12, 0, 0)
    upper1 = datetime(2020, 1, 1, 14, 0, 0)
    lower2 = datetime(2020, 1, 1, 13, 0, 0)
    upper2 = datetime(2020, 1, 1, 16, 0, 0)
    a1 = Appointment(since=lower1, until=upper1, accepted=False)
    a2 = Appointment(since=lower2, until=upper2, accepted=False)
    assert a1.collide(a2)
    assert a2.collide(a1)
