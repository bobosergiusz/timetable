from pytest import fixture
from tests.fakes import FakeUnitOfWork

from timetable.domain.event import Event
from timetable.domain.calendar import Calendar
from timetable.domain.command import Command
from timetable.bootstrap import bootstrap


@fixture
def test_mb():
    ev_s = []
    co_s = []
    mb = bootstrap(False, FakeUnitOfWork())
    mb.events_handlers = {Event: [lambda e: ev_s.append(e)]}
    mb.command_handlers = {Command: lambda c: co_s.append(c)}
    mb.ev_s = ev_s
    mb.co_s = co_s
    return mb


@fixture
def test_mb2():
    ev_s = []
    co_s = []
    mb = bootstrap(False, FakeUnitOfWork())

    def handle_command(c):
        co_s.append(c)
        mb.uow.calendars.list()[0].events.append(Event())

    mb.events_handlers = {Event: [lambda e: ev_s.append(e)]}
    mb.command_handlers = {Command: handle_command}
    mb.ev_s = ev_s
    mb.co_s = co_s
    return mb


class TestMessageBus:
    def test_message_bus_handles_event(self, test_mb):
        e = Event()
        print(test_mb.events_handlers)
        test_mb.handle(e)
        assert test_mb.ev_s == [e]
        assert test_mb.co_s == []

    def test_message_bus_handles_command(self, test_mb):
        c = Command()
        test_mb.handle(c)
        assert test_mb.ev_s == []
        assert test_mb.co_s == [c]

    def test_message_bus_process_added_events(self, test_mb2):
        cal = Calendar("bob")
        test_mb2.uow.calendars.add(cal)

        c = Command()
        test_mb2.handle(c)
        [o] = test_mb2.ev_s
        assert isinstance(o, Event)
        assert test_mb2.co_s == [c]
