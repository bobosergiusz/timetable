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
    pass


def test_uow_rolls_back_new_uncommited_appointment(Session):
    pass


def test_uow_rolls_back_new_appointment_on_error(Session):
    pass


def test_uow_rolls_back_uncommited_appointments_modification(Session):
    pass


def test_uow_rolls_back_appointment_modification_on_error(Session):
    pass
