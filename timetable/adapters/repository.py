from typing import List

from timetable.domain.appointment import Appointment
from timetable.domain.user import User


class DoesNotExistsError(BaseException):
    """No such appointment"""


class SqlRepository:
    def __init__(self, session):
        self.session = session

    def get(self, id: int) -> Appointment:
        app = self.session.query(Appointment).get(id)
        if app is None:
            raise DoesNotExistsError
        return app

    def list(self) -> List[Appointment]:
        return self.session.query(Appointment).all()

    def add(self, app: Appointment) -> None:
        self.session.add(app)


class SqlUserRepository:
    def __init__(self, session):
        self.session = session

    def get(self, account_name: str) -> User:
        us = self.session.query(User).get(account_name)
        if us is None:
            raise DoesNotExistsError
        return us

    def list(self) -> List[User]:
        return self.session.query(User).all()

    def add(self, us: User) -> None:
        self.session.add(us)
