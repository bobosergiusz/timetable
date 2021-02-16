from datetime import datetime

from timetable.domain.accept import (
    accept,
    build_exc_msg,
    find_colliding,
    NotAvailableError,
)
from timetable.domain.appointment import Appointment
from timetable.service_layer.unit_of_work import SqlUnitOfWork


def accept_appointment(id: int, uow: SqlUnitOfWork):
    with uow:
        app = uow.appointments.get(id)
        others = uow.appointments.list()
        accept(app, others)
        uow.commit()
        return app


def ask_appointment(since: datetime, until: datetime, uow: SqlUnitOfWork):
    app = Appointment(since=since, until=until, accepted=False)
    with uow:
        others = uow.appointments.list()
        colliding = find_colliding(app, others)
        try:
            n = next(colliding)
        except StopIteration:
            uow.appointments.add(app)
            uow.commit()
            return app
        else:
            msg = build_exc_msg(app, n, others)
            raise NotAvailableError(msg)
