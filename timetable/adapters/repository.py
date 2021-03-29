from typing import List

from timetable.domain.calendar import Calendar
from timetable.domain.user import User, Service

from timetable.domain.exceptions import DoesNotExistsError


class SqlCalendarRepository:
    def __init__(self, session):
        self.session = session

    def get(self, owner: str) -> Calendar:
        app = self.session.query(Calendar).get(owner)
        if app is None:
            raise DoesNotExistsError("service with this name does not exist")
        return app

    def list(self) -> List[Calendar]:
        return self.session.query(Calendar).all()

    def add(self, app: Calendar) -> None:
        self.session.add(app)


class SqlUserRepository:
    def __init__(self, session):
        self.session = session

    def get(self, account_name: str) -> User:
        us = self.session.query(User).get(account_name)
        if us is None:
            raise DoesNotExistsError("user with that name does not exist")
        return us

    def list(self) -> List[User]:
        return self.session.query(User).all()

    def list_services(self) -> List[Service]:
        return self.session.query(Service).all()

    def add(self, us: User) -> None:
        self.session.add(us)
