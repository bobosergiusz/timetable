from typing import Any, Dict, List

from timetable.domain.calendar import Calendar
from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError
from timetable.domain.user import Client, Service
from timetable.service_layer.unit_of_work import AbstractUnitOfWork

from timetable.domain.command import (
    CreateClient,
    CreateService,
    CreateAppointment,
    AcceptAppointment,
    GetUser,
    GetAppointment,
    ListAppointments,
    SearchServices,
)


def accept_appointment(
    aa: AcceptAppointment, uow: AbstractUnitOfWork
) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(aa.account_name)
        app = c.get_appointment(aa.id)
        app = c.accept_appointment(app)
        uow.commit()
        return app.to_dict()


def create_appointment(
    ca: CreateAppointment,
    uow: AbstractUnitOfWork,
) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(ca.to_user)
        a = c.create_appointment(
            ca.from_user, ca.since, ca.until, ca.description
        )
        uow.commit()
        return a.to_dict()


def list_appointments(
    la: ListAppointments, uow: AbstractUnitOfWork
) -> List[Dict[str, Any]]:
    with uow:
        c = uow.calendars.get(la.of_user)
        if la.for_user == la.of_user:
            apps = [a.to_dict() for a in c.list_appointments()]
        else:
            apps = [
                _mask(a.to_dict()) for a in c.list_appointments() if a.accepted
            ]
        return apps


def create_client(cc: CreateClient, uow: AbstractUnitOfWork) -> Dict[str, Any]:
    with uow:
        try:
            uow.users.get(cc.account_name)
        except DoesNotExistsError:
            u = Client(cc.account_name, cc.email, cc.password)
            uow.users.add(u)
            uow.commit()
            return u.to_dict()
        else:
            raise NotAvailableError


def create_service(
    cs: CreateService,
    uow: AbstractUnitOfWork,
) -> Dict[str, Any]:
    with uow:
        try:
            uow.users.get(cs.account_name)
        except DoesNotExistsError:
            u = Service(cs.account_name, cs.email, cs.password, cs.tags)
            uow.users.add(u)
            # FIX commit only once
            uow.commit()
            c = Calendar(owner=cs.account_name)
            uow.calendars.add(c)
            uow.commit()
            return u.to_dict()
        else:
            raise NotAvailableError


def get_user(ga: GetUser, uow: AbstractUnitOfWork) -> Dict[str, Any]:
    with uow:
        u = uow.users.get(ga.account_name)
        return u.to_dict()


def search_services(
    ss: SearchServices, uow: AbstractUnitOfWork
) -> List[Dict[str, Any]]:
    with uow:
        us = uow.users.list_services()
        for t in ss.tags:
            us = [u for u in us if t in u.tags]
        us_masked = [_mask_service(u.to_dict()) for u in us]
        return us_masked


def get_appointment(
    ga: GetAppointment, uow: AbstractUnitOfWork
) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(ga.account_name)
        app = c.get_appointment(ga.id)
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
