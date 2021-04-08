from typing import Dict, Union, Callable, List, Type, Any, TypeVar
import logging

from timetable.domain.event import Event
from timetable.domain.command import (
    Command,
    CreateAppointment,
    AcceptAppointment,
    CreateService,
    CreateClient,
)
from timetable.service_layer.unit_of_work import AbstractUnitOfWork
from timetable.service_layer.handlers import (
    create_appointment,
    accept_appointment,
    create_client,
    create_service,
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
        CreateClient: create_client,
        CreateService: create_service,
    }

    def handle(self, message: Message, uow: AbstractUnitOfWork):
        queue = [message]
        while queue:
            message = queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, Command):
                self.handle_command(message, queue, uow)
            else:
                raise Exception(f"{message} was not an Event or Command")

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
            handler(command, uow)
        except Exception:
            logger.exception(f"Exception handling command {command}")
            raise
        else:
            queue.extend(uow.collect_new_events())
