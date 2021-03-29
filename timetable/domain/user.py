from dataclasses import dataclass
from typing import List, Any, Dict


@dataclass
class User:
    """This is a base class for users, should not be instatiated."""

    account_name: str
    email: str
    password: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_name": self.account_name,
            "email": self.email,
            "password": self.password,
        }


class Client(User):
    """This is concrete implementation for a plain user."""


@dataclass
class Service(User):
    """This is concrete implementation for user providing a service."""

    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return dict(super().to_dict(), **{"tags": [t for t in self.tags]})
