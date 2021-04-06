from tests.fakes import FakeUnitOfWork

from timetable.domain.event import Event
from timetable.domain.calendar import Calendar
from timetable.domain.command import Command
from timetable.service_layer.message_bus import MessageBus


class TestMessageBus:
    def test_message_bus_handles_event(self):
        ev_s = []
        co_s = []
        m = MessageBus()
        m.EVENT_HANDLERS = {Event: [lambda e, _: ev_s.append(e)]}
        m.COMMAND_HANDLERS = {Command: lambda e, _: co_s.append(e)}
        e = Event()
        uow = FakeUnitOfWork()
        m.handle(e, uow)
        assert ev_s == [e]
        assert co_s == []

    def test_message_bus_handles_command(self):
        ev_s = []
        co_s = []
        m = MessageBus()
        m.EVENT_HANDLERS = {Event: [lambda e, _: ev_s.append(e)]}
        m.COMMAND_HANDLERS = {Command: lambda e, _: co_s.append(e)}
        c = Command()
        uow = FakeUnitOfWork()
        m.handle(c, uow)
        assert ev_s == []
        assert co_s == [c]

    def test_message_bus_process_added_events(self):
        cal = Calendar("bob")
        uow = FakeUnitOfWork()
        uow.calendars.add(cal)
        ev_s = []
        co_s = []
        m = MessageBus()
        c = Command()
        e = Event()

        def handle_event(e, uow):
            ev_s.append(e)
            uow.calendars.list()[0].events.append(c)

        m.EVENT_HANDLERS = {Event: [handle_event]}
        m.COMMAND_HANDLERS = {Command: lambda e, _: co_s.append(e)}
        m.handle(e, uow)
        assert ev_s == [e]
        assert co_s == [c]
