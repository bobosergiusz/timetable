from typing import List

from timetable.model.appointment import Appointment


class NotAvailableError(BaseException):
    """There is appointment during this time"""


def accept(app: Appointment, others: List[Appointment]):
    for app2 in others:
        if app2.accepted and app.collide(app2):
            raise NotAvailableError(f"{app} collides with {app2}")
    app.accepted = True
