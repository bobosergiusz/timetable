from datetime import datetime

from timetable.domain.calendar import Calendar
from timetable.service_layer.unit_of_work import SqlUnitOfWork


from tests.utils import insert_appointment, insert_calendar


class FakeEvent:
    """FakeEvent"""


class TestUnitOfWork:
    def test_uow_can_create_calendar(self, Session):
        uow = SqlUnitOfWork(Session)

        owner = "bob"

        with uow:
            c = Calendar(owner=owner)
            uow.calendars.add(c)
            uow.commit()

        session = Session()
        [[owner_retrieved]] = session.execute("SELECT owner FROM calendars")
        assert owner_retrieved == c.owner

    def test_uow_can_retrieve_and_modify_calendar(self, Session):
        s = Session()
        owner = "bob"
        insert_calendar(s, owner)

        from_user = "john"
        since = datetime(2000, 1, 1)
        until = datetime(2000, 1, 2)
        description = "rapair my car"
        insert_appointment(
            s, owner, from_user, since, until, description, False
        )

        [[id_appointment]] = s.execute("SELECT id FROM appointments")

        uow = SqlUnitOfWork(Session)
        with uow:
            c = uow.calendars.get(owner)
            a = c.get_appointment(id_appointment)
            a = c.accept_appointment(a)
            uow.commit()

        [[accepted_retrieved]] = s.execute("SELECT accepted FROM appointments")
        assert accepted_retrieved

    def test_uow_rolls_back_uncommited_changes(self, Session):
        s = Session()
        owner = "bob"
        insert_calendar(s, owner)

        from_user = "john"
        since = datetime(2000, 1, 1)
        until = datetime(2000, 1, 2)
        description = "rapair my car"
        insert_appointment(
            s, owner, from_user, since, until, description, False
        )

        [[id_appointment]] = s.execute("SELECT id FROM appointments")

        uow = SqlUnitOfWork(Session)
        with uow:
            c = uow.calendars.get(owner)
            a = c.get_appointment(id_appointment)
            a = c.accept_appointment(a)

        [[accepted_retrieved]] = s.execute("SELECT accepted FROM appointments")
        assert not accepted_retrieved

    def test_uow_rolls_back_new_appointment_on_error(self, Session):
        s = Session()
        owner = "bob"
        insert_calendar(s, owner)

        from_user = "john"
        since = datetime(2000, 1, 1)
        until = datetime(2000, 1, 2)
        description = "rapair my car"
        insert_appointment(
            s, owner, from_user, since, until, description, False
        )

        [[id_appointment]] = s.execute("SELECT id FROM appointments")

        uow = SqlUnitOfWork(Session)
        try:
            with uow:
                c = uow.calendars.get(owner)
                a = c.get_appointment(id_appointment)
                a = c.accept_appointment(a)
                raise ArithmeticError
        except ArithmeticError:
            pass

        [[accepted_retrieved]] = s.execute("SELECT accepted FROM appointments")
        assert not accepted_retrieved

    def test_uow_yields_events(self, Session):
        s = Session()
        owner = "bob"
        insert_calendar(s, owner)

        ev1 = FakeEvent()
        ev2 = FakeEvent()

        uow = SqlUnitOfWork(Session)
        with uow:
            c = uow.calendars.get(owner)
            c.events.append(ev1)
            c.events.append(ev2)
            uow.commit()
            events_collected = set(uow.collect_new_events())

        assert events_collected == {ev1, ev2}
