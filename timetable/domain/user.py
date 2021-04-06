from dataclasses import dataclass, field
from typing import List, Any, Dict


@dataclass(unsafe_hash=True)
class User:
    """This is a base class for users, should not be instatiated."""

    account_name: str
    email: str = field(compare=False)
    password: str = field(compare=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_name": self.account_name,
            "email": self.email,
            "password": self.password,
        }


@dataclass(unsafe_hash=True)
class Client(User):
    """This is concrete implementation for a plain user."""


@dataclass(unsafe_hash=True)
class Service(User):
    """This is concrete implementation for user providing a service."""

    tags: List[str] = field(compare=False)

    def to_dict(self) -> Dict[str, Any]:
        return dict(super().to_dict(), **{"tags": [t for t in self.tags]})
