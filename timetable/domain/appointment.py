from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class Appointment:
    def __init__(
        self,
        id: Optional[int],
        from_user: str,
        since: datetime,
        until: datetime,
        description: str,
        accepted: bool,
    ):
        if (until - since) <= timedelta():
            raise ValueError(
                f"since cannot be after until ({since} > {until})"
            )
        self.id = id
        self.from_user = from_user
        self.since = since
        self.until = until
        self.description = description
        self.accepted = accepted

    def collide(self, other: "Appointment") -> bool:
        return (self != other) and (
            ((self.since <= other.since) and (other.since < self.until))
            or ((self.since < other.until) and (other.until <= self.until))
            or ((self.since > other.since) and (other.until > self.until))
        )

    def __repr__(self) -> str:
        return f"Appointment({self.since}, {self.until})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_user": self.from_user,
            "since": self.since,
            "until": self.until,
            "description": self.description,
            "accepted": self.accepted,
        }
