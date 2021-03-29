from datetime import datetime
from typing import List

from timetable.domain.appointment import Appointment
from timetable.domain.exceptions import DoesNotExistsError, NotAvailableError


class Calendar:
    def __init__(self, owner: str):
        self.id_count = 0
        self._appointments: List[Appointment] = []
        self.owner = owner

    def create_appointment(
        self,
        from_user: str,
        since: datetime,
        until: datetime,
        description: str,
    ) -> Appointment:
        a = Appointment(
            id=self.id_count,
            from_user=from_user,
            since=since,
            until=until,
            description=description,
            accepted=False,
        )
        for a2 in self._appointments:
            if a2.collide(a) and a2.accepted:
                raise NotAvailableError
        self._appointments.append(a)
        self.id_count += 1
        return a

    def accept_appointment(self, a: Appointment) -> Appointment:
        updated_list: List[Appointment] = []
        owned = False
        for i, a2 in enumerate(self._appointments):
            self._resolve_collision(a, a2, updated_list)
            if a2 == a:
                owned = True
        if not owned:
            raise DoesNotExistsError(
                "This element does not belong to this calendar"
            )
        self._appointments = updated_list
        a.accepted = True
        return a

    def _resolve_collision(
        self,
        a1: Appointment,
        a2: Appointment,
        verified_list: List[Appointment],
    ):
        if a2.collide(a1):
            if a2.accepted:
                raise NotAvailableError
        else:
            verified_list.append(a2)

    def __repr__(self) -> str:
        return "Calendar()"

    # TODO: These two methods may be better to be moved to other module (CQRS)

    def list_appointments(self) -> List[Appointment]:
        return self._appointments

    def get_appointment(self, id: int) -> Appointment:
        app = next((a for a in self._appointments if a.id == id), None)
        if app is None:
            raise DoesNotExistsError("such appointment does not exists")
        return app
