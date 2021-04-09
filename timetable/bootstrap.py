import inspect
from functools import partial

from timetable.adapters.orm import start_mappers
from timetable.service_layer.message_bus import MessageBus
from timetable.service_layer.unit_of_work import AbstractUnitOfWork

from timetable.service_layer.handlers import EVENT_HANDLERS, COMMAND_HANDLERS


def bootstrap(start_orm: bool, uow: AbstractUnitOfWork) -> MessageBus:
    if start_orm:
        start_mappers()

    dependencies = {"uow": uow}

    events_handlers = {
        event: inject_dependencies(handler, dependencies)
        for event, handler in EVENT_HANDLERS.items()
    }
    command_handlers = {
        event: inject_dependencies(handler, dependencies)
        for event, handler in COMMAND_HANDLERS.items()
    }

    mb = MessageBus(events_handlers, command_handlers, uow)
    return mb


def inject_dependencies(target, dependencies):
    params = inspect.signature(target).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return partial(target, **deps)
