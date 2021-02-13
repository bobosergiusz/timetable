from datetime import datetime, timedelta

import pytest


from timetable.model.accept import accept, NotAvailableError
from timetable.model.appointment import Appointment


def test_can_accept_if_no_appoinment_at_the_time():
    lower = datetime(2020, 1, 1, 12, 0, 0)
    upper = lower + timedelta(hours=1)
    i = Appointment(since=lower, until=upper, accepted=False)

    accept(i, [])
    assert i.accepted


def test_can_accept_if_no_appointment_collide():
    lower_inq = datetime(2020, 1, 1, 12, 0, 0)
    upper_inq = lower_inq + timedelta(hours=1)
    lower_app1 = lower_inq + timedelta(hours=1)
    upper_app1 = lower_inq + timedelta(hours=3)
    lower_app2 = lower_inq + timedelta(hours=-1)
    upper_app2 = lower_inq
    i = Appointment(since=lower_inq, until=upper_inq, accepted=False)
    av1 = Appointment(since=lower_app1, until=upper_app1, accepted=True)
    av2 = Appointment(since=lower_app2, until=upper_app2, accepted=True)

    accept(i, [av1, av2])
    assert i.accepted


def test_cannot_accept_if_appointment_collide():
    lower_inq = datetime(2020, 1, 1, 12, 0, 0)
    upper_inq = lower_inq + timedelta(hours=3)
    lower_app = lower_inq + timedelta(hours=1)
    upper_app = lower_inq + timedelta(hours=2)
    i = Appointment(since=lower_inq, until=upper_inq, accepted=False)
    av = Appointment(since=lower_app, until=upper_app, accepted=True)

    with pytest.raises(NotAvailableError):
        accept(i, [av])
