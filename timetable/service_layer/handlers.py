from typing import List, Dict, Type, Callable

from timetable.domain.calendar import Calendar
from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError
from timetable.domain.user import Client, Service
from timetable.service_layer.unit_of_work import AbstractUnitOfWork


from timetable.domain.event import Event
from timetable.domain.command import Command


from timetable.domain.command import (
    CreateClient,
    CreateService,
    CreateAppointment,
    AcceptAppointment,
)


def accept_appointment(aa: AcceptAppointment, uow: AbstractUnitOfWork):
    with uow:
        c = uow.calendars.get(aa.account_name)
        app = c.get_appointment(aa.id)
        c.accept_appointment(app)
        uow.commit()


def create_appointment(
    ca: CreateAppointment,
    uow: AbstractUnitOfWork,
):
    with uow:
        c = uow.calendars.get(ca.to_user)
        c.create_appointment(ca.from_user, ca.since, ca.until, ca.description)
        uow.commit()


def create_client(cc: CreateClient, uow: AbstractUnitOfWork):
    with uow:
        try:
            uow.users.get(cc.account_name)
        except DoesNotExistsError:
            u = Client(cc.account_name, cc.email, cc.password)
            uow.users.add(u)
            uow.commit()
        else:
            raise NotAvailableError


def create_service(
    cs: CreateService,
    uow: AbstractUnitOfWork,
):
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
        else:
            raise NotAvailableError


EVENT_HANDLERS: Dict[Type[Event], List[Callable]] = {}
COMMAND_HANDLERS: Dict[Type[Command], Callable] = {
    CreateAppointment: create_appointment,
    AcceptAppointment: accept_appointment,
    CreateClient: create_client,
    CreateService: create_service,
}
