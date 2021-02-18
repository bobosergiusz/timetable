from typing import Iterator, List

from timetable.domain.appointment import Appointment


class NotAvailableError(BaseException):
    """There is appointment during this time"""


def find_colliding(
    app: Appointment, others: List[Appointment]
) -> Iterator[Appointment]:
    for app2 in others:
        if app2.accepted and app.collide(app2):
            yield app2


def accept(app: Appointment, others: List[Appointment]) -> None:
    colliding = find_colliding(app, others)
    try:
        n = next(colliding)
    except StopIteration:
        app.accepted = True
    else:
        msg = build_exc_msg(app, n, colliding)
        raise NotAvailableError(msg)


def build_exc_msg(
    app: Appointment, app1: Appointment, others: Iterator[Appointment]
) -> str:
    msg = f"{app} collides with {app1}"
    rest = ", ".join(str(c) for c in others)
    if rest:
        msg = f"{msg}, {rest}"
    return msg
