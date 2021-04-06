from timetable.adapters.repository import (
    AbstractRepository,
    UserRepository,
    SqlTrackingCalendarRepository,
    SqlTrackingUserRepository,
)
from timetable.domain.calendar import Calendar


class AbstractUnitOfWork:
    calendars: AbstractRepository[Calendar]
    users: UserRepository

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, type, value, traceback):
        self.rollback()

    def rollback(self):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def collect_new_events(self):
        for calendar in self.calendars.seen:
            while calendar.events:
                yield calendar.events.pop(0)


class SqlUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.calendars = SqlTrackingCalendarRepository(self.session)
        self.users = SqlTrackingUserRepository(self.session)
        return self

    def rollback(self):
        self.session.rollback()

    def commit(self):
        self.session.commit()
