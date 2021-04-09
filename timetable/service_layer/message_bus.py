from typing import Union, List, Dict, Type, Callable
import logging

from timetable.domain.event import Event
from timetable.domain.command import Command
from timetable.service_layer.unit_of_work import AbstractUnitOfWork

Message = Union[Command, Event]

logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(
        self,
        events_handlers: Dict[Type[Event], List[Callable[[Event], None]]],
        command_handlers: Dict[Type[Command], Callable[[Command], None]],
        uow: AbstractUnitOfWork,
    ):
        self.events_handlers = events_handlers
        self.command_handlers = command_handlers
        self.uow = uow

    def handle(self, message: Message):
        queue = [message]
        while queue:
            message = queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message, queue)
            elif isinstance(message, Command):
                self.handle_command(message, queue)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: Event, queue: List[Message]):
        for handler in self.events_handlers[type(event)]:
            logger.debug(f"handling event {event} with handler {handler}")
            try:
                handler(event)
            except Exception:
                logger.exception(f"Exception handling event {event}")
            else:
                queue.extend(self.uow.collect_new_events())

    def handle_command(self, command: Command, queue: List[Message]):
        logger.debug(f"handling command {command}")
        handler = self.command_handlers[type(command)]
        try:
            handler(command)
        except Exception:
            logger.exception(f"Exception handling command {command}")
            raise
        else:
            queue.extend(self.uow.collect_new_events())
