from typing import List
from timetable.domain.appointment import Appointment


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
        return self.session.query(Appointment).list()

    def add(self, app: Appointment) -> None:
        self.session.add(app)
