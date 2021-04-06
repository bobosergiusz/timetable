from datetime import datetime
from dataclasses import dataclass
from typing import List


class Command:
    """Base class for commands"""


@dataclass
class CreateAppointment(Command):
    to_user: str
    from_user: str
    since: datetime
    until: datetime
    description: str


@dataclass
class AcceptAppointment(Command):
    account_name: str
    id: int


@dataclass
class ListAppointments(Command):
    of_user: str
    for_user: str


@dataclass
class CreateClient(Command):
    account_name: str
    email: str
    password: str


@dataclass
class CreateService(Command):
    account_name: str
    email: str
    password: str
    tags: List[str]


@dataclass
class GetUser(Command):
    account_name: str


@dataclass
class GetAppointment(Command):
    account_name: str
    id: int


@dataclass
class SearchServices(Command):
    tags: List[str]
