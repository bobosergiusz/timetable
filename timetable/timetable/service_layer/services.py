from datetime import datetime
from typing import Any, Dict, List

from timetable.domain.accept import (
    accept,
    build_exc_msg,
    find_colliding,
    NotAvailableError,
)
from timetable.domain.appointment import Appointment
from timetable.service_layer.unit_of_work import SqlUnitOfWork


def accept_appointment(id: int, uow: SqlUnitOfWork) -> Dict[str, Any]:
    with uow:
        app = uow.appointments.get(id)
        others = uow.appointments.list()
        accept(app, others)
        uow.commit()
        return app.to_dict()


def ask_appointment(
    since: datetime, until: datetime, uow: SqlUnitOfWork
) -> Dict[str, Any]:
    app = Appointment(since=since, until=until, accepted=False)
    with uow:
        others = uow.appointments.list()
        colliding = find_colliding(app, others)
        try:
            n = next(colliding)
        except StopIteration:
            uow.appointments.add(app)
            uow.commit()
            return app.to_dict()
        else:
            msg = build_exc_msg(app, n, others)
            raise NotAvailableError(msg)


def list_appointments(uow: SqlUnitOfWork) -> List[Dict[str, Any]]:
    with uow:
        list_apps = uow.appointments.list()
        return [app.to_dict() for app in list_apps]
