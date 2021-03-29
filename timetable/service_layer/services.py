from datetime import datetime
from typing import Any, Dict, List

from timetable.domain.calendar import Calendar
from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError
from timetable.domain.user import Client, Service
from timetable.service_layer.unit_of_work import SqlUnitOfWork


def accept_appointment(
    to_user: str, id: int, uow: SqlUnitOfWork
) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(to_user)
        app = c.get_appointment(id)
        app = c.accept_appointment(app)
        uow.commit()
        return app.to_dict()


def create_appointment(
    to_user: str,
    from_user: str,
    since: datetime,
    until: datetime,
    description: str,
    uow: SqlUnitOfWork,
) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(to_user)
        a = c.create_appointment(from_user, since, until, description)
        uow.commit()
        return a.to_dict()


def list_appointments_owned(
    account_name: str, uow: SqlUnitOfWork
) -> List[Dict[str, Any]]:
    with uow:
        c = uow.calendars.get(account_name)
        apps = [a.to_dict() for a in c.list_appointments()]
        return apps


def list_appointments_unowned(
    account_name: str, uow: SqlUnitOfWork
) -> List[Dict[str, Any]]:
    with uow:
        c = uow.calendars.get(account_name)
        apps = [_mask(a.to_dict()) for a in c.list_appointments()]
        return apps


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
            # FIX commit only once
            uow.commit()
            c = Calendar(owner=account_name)
            uow.calendars.add(c)
            uow.commit()
            return u.to_dict()
        else:
            raise NotAvailableError


def get_user(account_name: str, uow) -> Dict[str, Any]:
    with uow:
        u = uow.users.get(account_name)
        return u.to_dict()


def search_services(tags: List[str], uow) -> Dict[str, Any]:
    with uow:
        us = uow.users.list_services()
        for t in tags:
            us = [u for u in us if t in u.tags]
        us = [_mask_service(u.to_dict()) for u in us]
        return us


def get_appointment(account_name: str, app_id: int, uow) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(account_name)
        app = c.get_appointment(app_id)
        return app.to_dict()


def _mask_service(u: Dict[str, Any]) -> Dict[str, Any]:
    masked = dict()
    masked["account_name"] = u["account_name"]
    masked["tags"] = u["tags"]
    return masked


def _mask(app: Dict[str, Any]) -> Dict[str, str]:
    masked = dict()
    masked["since"] = app["since"]
    masked["until"] = app["until"]
    return masked
