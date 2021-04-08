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
