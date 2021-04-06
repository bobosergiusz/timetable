from typing import List, Generic, TypeVar, Type

from timetable.domain.calendar import Calendar
from timetable.domain.user import User, Service

from timetable.domain.exceptions import DoesNotExistsError

T = TypeVar("T")


class AbstractRepository(Generic[T]):
    def __init__(self, session):
        raise NotImplementedError

    def get(self, id: str) -> T:
        raise NotImplementedError

    def list(self) -> List[T]:
        raise NotImplementedError

    def add(self, c: T) -> None:
        raise NotImplementedError


class UserRepository(AbstractRepository[User]):
    def list_services(self) -> List[Service]:
        raise NotImplementedError


class SqlRepository(AbstractRepository, Generic[T]):
    model: T

    def __init__(self, session):
        self.session = session

    def get(self, id: str) -> T:
        t = self.session.query(self.model).get(id)
        if t is None:
            raise DoesNotExistsError(
                f"{self.model} with this id does not exist"
            )
        return t

    def list(self) -> List[T]:
        all_ = self.session.query(self.model).all()
        return all_

    def add(self, t: T) -> None:
        self.session.add(t)


class SqlCalendarRepository(SqlRepository):
    model = Calendar


class SqlUserRepository(SqlRepository, UserRepository):
    model = User

    def list_services(self) -> List[Service]:
        all_ = self.session.query(Service).all()
        return all_


class TrackingRepository(Generic[T]):
    repo_class: Type[AbstractRepository[T]]

    def __init__(self, *args):
        self.repo = self.repo_class(*args)
        self.seen = set()

    def get(self, id: str) -> T:
        t = self.repo.get(id)
        self.seen.add(t)
        return t

    def list(self) -> List[T]:
        all_ = self.repo.list()
        self.seen.update(all_)
        return all_

    def add(self, t: T) -> None:
        self.seen.add(t)
        self.repo.add(t)


class SqlTrackingCalendarRepository(TrackingRepository):
    repo_class = SqlCalendarRepository


class SqlTrackingUserRepository(TrackingRepository):
    repo_class = SqlUserRepository

    def list_services(self) -> List[Service]:
        all_ = self.repo.list_services()
        self.seen.update(all_)
        return all_
