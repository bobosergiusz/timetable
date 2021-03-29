from datetime import datetime


from timetable.domain.appointment import Appointment


def test_separate_not_collide():
    lower1 = datetime(2020, 1, 1, 12, 0, 0)
    upper1 = datetime(2020, 1, 1, 13, 0, 0)
    lower2 = datetime(2020, 1, 1, 14, 0, 0)
    upper2 = datetime(2020, 1, 1, 16, 0, 0)
    a1 = Appointment(
        id=1,
        from_user="bob",
        since=lower1,
        until=upper1,
        description="appointment",
        accepted=True,
    )
    a2 = Appointment(
        id=2,
        from_user="john",
        since=lower2,
        until=upper2,
        description="car repair",
        accepted=True,
    )
    assert not a1.collide(a2)
    assert not a2.collide(a1)


def test_next_to_not_collide():
    lower1 = datetime(2020, 1, 1, 12, 0, 0)
    upper1 = datetime(2020, 1, 1, 13, 0, 0)
    lower2 = datetime(2020, 1, 1, 13, 0, 0)
    upper2 = datetime(2020, 1, 1, 16, 0, 0)
    a1 = Appointment(
        id=1,
        from_user="bob",
        since=lower1,
        until=upper1,
        description="appointment",
        accepted=True,
    )
    a2 = Appointment(
        id=2,
        from_user="john",
        since=lower2,
        until=upper2,
        description="car repair",
        accepted=True,
    )
    assert not a1.collide(a2)
    assert not a2.collide(a1)


def test_collide():
    lower1 = datetime(2020, 1, 1, 12, 0, 0)
    upper1 = datetime(2020, 1, 1, 14, 0, 0)
    lower2 = datetime(2020, 1, 1, 13, 0, 0)
    upper2 = datetime(2020, 1, 1, 16, 0, 0)
    a1 = Appointment(
        id=1,
        from_user="bob",
        since=lower1,
        until=upper1,
        description="appointment",
        accepted=False,
    )
    a2 = Appointment(
        id=2,
        from_user="john",
        since=lower2,
        until=upper2,
        description="car repair",
        accepted=False,
    )
    assert a1.collide(a2)
    assert a2.collide(a1)


def test_does_not_collide_with_self():
    lower = datetime(2020, 1, 1, 12, 0, 0)
    upper = datetime(2020, 1, 1, 14, 0, 0)
    a = Appointment(
        id=1,
        from_user="bob",
        since=lower,
        until=upper,
        description="appointment",
        accepted=False,
    )
    assert not a.collide(a)
