from datetime import datetime
from typing import Any, Dict, List

from timetable.domain.accept import (
    accept,
    build_exc_msg,
    find_colliding,
    NotAvailableError,
)
from timetable.domain.appointment import Appointment
from timetable.domain.user import Client, Service
from timetable.service_layer.unit_of_work import SqlUnitOfWork
from timetable.adapters.repository import DoesNotExistsError


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


def create_client(
    account_name: str, email: str, password: str, uow: SqlUnitOfWork
) -> Dict[str, Any]:
    with uow:
        try:
            uow.users.get(account_name)
        except DoesNotExistsError:
            u = Client(account_name, email, password)
            uow.users.add(u)
            uow.commit()
            return u.to_dict()
        else:
            raise NotAvailableError


def create_service(
    account_name: str,
    email: str,
    password: str,
    tags: List[str],
    uow: SqlUnitOfWork,
) -> Dict[str, Any]:
    with uow:
        try:
            uow.users.get(account_name)
        except DoesNotExistsError:
            u = Service(account_name, email, password, tags)
            uow.users.add(u)
            uow.commit()
            return u.to_dict()
        else:
            raise NotAvailableError


def get_user(account_name: str, uow) -> Dict[str, Any]:
    with uow:
        u = uow.users.get(account_name)
        return u.to_dict()
