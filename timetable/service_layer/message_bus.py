from typing import Dict, Union, Callable, List, Type, Any, TypeVar
import logging

from timetable.domain.event import Event
from timetable.domain.command import (
    Command,
    CreateAppointment,
    AcceptAppointment,
    SearchServices,
    GetAppointment,
    GetUser,
    CreateService,
    CreateClient,
    ListAppointments,
)
from timetable.service_layer.unit_of_work import AbstractUnitOfWork
from timetable.service_layer.handlers import (
    create_appointment,
    accept_appointment,
    list_appointments,
    create_client,
    create_service,
    get_user,
    get_appointment,
    search_services,
)

Message = Union[Command, Event]

logger = logging.getLogger(__name__)


CommandT = TypeVar("CommandT", bound=Command)
rv = Callable[
    [CommandT, AbstractUnitOfWork],
    Union[List[Dict[str, Any]], Dict[str, Any]],
]


class MessageBus:
    EVENT_HANDLERS: Dict[
        Type[Event], List[Callable[[Event, AbstractUnitOfWork], None]]
    ] = {}
    COMMAND_HANDLERS: Dict[Type[Command], rv] = {
        CreateAppointment: create_appointment,
        AcceptAppointment: accept_appointment,
        ListAppointments: list_appointments,
        CreateClient: create_client,
        CreateService: create_service,
        GetUser: get_user,
        GetAppointment: get_appointment,
        SearchServices: search_services,
    }

    def handle(self, message: Message, uow: AbstractUnitOfWork):
        results = []
        queue = [message]
        while queue:
            message = queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, Command):
                cmd_result = self.handle_command(message, queue, uow)
                results.append(cmd_result)
            else:
                raise Exception(f"{message} was not an Event or Command")
        return results

    def handle_event(
        self, event: Event, queue: List[Message], uow: AbstractUnitOfWork
    ):
        for handler in self.EVENT_HANDLERS[type(event)]:
            logger.debug(f"handling event {event} with handler {handler}")
            try:
                handler(event, uow)
            except Exception:
                logger.exception(f"Exception handling event {event}")
            else:
                queue.extend(uow.collect_new_events())

    def handle_command(
        self, command: Command, queue: List[Message], uow: AbstractUnitOfWork
    ):
        logger.debug(f"handling command {command}")
        handler = self.COMMAND_HANDLERS[type(command)]
        try:
            result = handler(command, uow)
        except Exception:
            logger.exception(f"Exception handling command {command}")
            raise
        else:
            queue.extend(uow.collect_new_events())
            return result
