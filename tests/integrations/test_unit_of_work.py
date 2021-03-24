from datetime import datetime

from timetable.domain.appointment import Appointment
from timetable.service_layer.unit_of_work import SqlUnitOfWork


from tests.utils import insert_appointment


def test_uow_can_create_appointment(Session):
    uow = SqlUnitOfWork(Session)

    since = datetime(2000, 1, 1)
    until = datetime(2000, 1, 2)

    with uow:
        a = Appointment(since=since, until=until, accepted=False)
        uow.appointments.add(a)
        uow.commit()

    session = Session()
    [[since_retrieved, until_retrieved, accepted_retrieved]] = session.execute(
        "SELECT since, until, accepted FROM appointments"
    )
    assert since_retrieved == a.since.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert until_retrieved == a.until.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert accepted_retrieved == a.accepted


def test_uow_can_retrieve_and_modify_appointment(Session):
    since = datetime(2000, 1, 1)
    until = datetime(2000, 1, 2)
    s = Session()
    insert_appointment(s, since, until, True)

    [[id_]] = s.execute("SELECT id FROM appointments")

    uow = SqlUnitOfWork(Session)
    with uow:
        a = uow.appointments.get(id_)
        since_modified = datetime(2001, 1, 1)
        until_modified = datetime(2001, 1, 2)
        a.since = since_modified
        a.until = until_modified
        a.accepted = False
        uow.commit()

    session = Session()
    [[since_retrieved, until_retrieved, accepted_retrieved]] = session.execute(
        "SELECT since, until, accepted FROM appointments"
    )
    assert since_retrieved == since_modified.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert until_retrieved == until_modified.strftime("%Y-%m-%d %H:%M:%S.%f")
    assert accepted_retrieved == a.accepted


def test_uow_rolls_back_new_uncommited_appointment(Session):
    uow = SqlUnitOfWork(Session)

    since = datetime(2000, 1, 1)
    until = datetime(2000, 1, 2)

    session = Session()
    appointments_pre = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )

    with uow:
        a = Appointment(since=since, until=until, accepted=False)
        uow.appointments.add(a)

    appointments_post = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )
    assert appointments_pre == appointments_post


def test_uow_rolls_back_new_appointment_on_error(Session):
    uow = SqlUnitOfWork(Session)

    since = datetime(2000, 1, 1)
    until = datetime(2000, 1, 2)

    session = Session()
    appointments_pre = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )

    try:
        with uow:
            a = Appointment(since=since, until=until, accepted=False)
            uow.appointments.add(a)
            raise ArithmeticError
    except ArithmeticError:
        pass

    appointments_post = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )
    assert appointments_pre == appointments_post


def test_uow_rolls_back_uncommited_appointments_modification(Session):
    since = datetime(2000, 1, 1)
    until = datetime(2000, 1, 2)
    s = Session()
    insert_appointment(s, since, until, True)

    [[id_]] = s.execute("SELECT id FROM appointments")

    session = Session()
    appointments_pre = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )

    uow = SqlUnitOfWork(Session)
    with uow:
        a = uow.appointments.get(id_)
        since_modified = datetime(2001, 1, 1)
        until_modified = datetime(2001, 1, 2)
        a.since = since_modified
        a.until = until_modified
        a.accepted = False

    appointments_post = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )
    assert appointments_pre == appointments_post


def test_uow_rolls_back_appointment_modification_on_error(Session):
    since = datetime(2000, 1, 1)
    until = datetime(2000, 1, 2)
    s = Session()
    insert_appointment(s, since, until, True)

    [[id_]] = s.execute("SELECT id FROM appointments")

    session = Session()
    appointments_pre = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )

    uow = SqlUnitOfWork(Session)
    try:
        with uow:
            a = uow.appointments.get(id_)
            since_modified = datetime(2001, 1, 1)
            until_modified = datetime(2001, 1, 2)
            a.since = since_modified
            a.until = until_modified
            a.accepted = False
            raise ArithmeticError
    except ArithmeticError:
        pass

    appointments_post = list(
        session.execute("SELECT since, until, accepted FROM appointments")
    )
    assert appointments_pre == appointments_post
