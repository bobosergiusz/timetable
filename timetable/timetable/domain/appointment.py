from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class Appointment:
    def __init__(
        self,
        since: datetime,
        until: datetime,
        accepted: bool,
        id: Optional[int] = None,
    ):
        if (until - since) <= timedelta():
            raise ValueError(
                f"since cannot be after until ({since} > {until})"
            )
        self.id = id
        self.since = since
        self.until = until
        self.accepted = accepted

    def collide(self, other: "Appointment") -> bool:
        return (
            ((self.since <= other.since) and (other.since < self.until))
            or ((self.since < other.until) and (other.until <= self.until))
            or ((self.since > other.since) and (other.until > self.until))
        )

    def __repr__(self) -> str:
        return f"Appointment({self.since}, {self.until})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "since": self.since,
            "until": self.until,
            "accepted": self.accepted,
        }
