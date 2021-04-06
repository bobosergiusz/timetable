from timetable.adapters.repository import (
    AbstractRepository,
    TrackingRepository,
)
from timetable.domain.exceptions import DoesNotExistsError
from timetable.domain.user import Service
from timetable.service_layer.unit_of_work import AbstractUnitOfWork


class FakeRepository(AbstractRepository):
    def __init__(self, obs):
        self.obs = obs

    def get(self, id):
        ob = next(
            (ob for ob in self.obs if getattr(ob, self.id_attr) == id), None
        )
        if ob is None:
            raise DoesNotExistsError
        return ob

    def list(self):
        return self.obs

    def add(self, ob):
        id = getattr(ob, self.id_attr)
        i = next(
            (
                i
                for i, o in enumerate(self.obs)
                if getattr(o, self.id_attr) == id
            ),
            None,
        )
        if i is None:
            self.obs.append(ob)
        else:
            self.obs[i] = ob


class FakeCalendarRepository(FakeRepository):
    id_attr = "owner"


class FakeTrackingCalendarRepository(TrackingRepository):
    repo_class = FakeCalendarRepository


class FakeUsersRepository(FakeRepository):
    id_attr = "account_name"

    def list_services(self):
        filtered = [u for u in self.obs if isinstance(u, Service)]
        return filtered


class FakeTrackingUserRepository(TrackingRepository):
    repo_class = FakeUsersRepository

    def list_services(self):
        filtered = self.repo.list_services()
        self.seen.update(filtered)
        return filtered


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.commited = False
        self.calendars = FakeTrackingCalendarRepository([])
        self.users = FakeTrackingUserRepository([])
        self.events = []

    def __enter__(self):
        return self

    def rollback(self):
        pass

    def commit(self):
        self.commited = True
