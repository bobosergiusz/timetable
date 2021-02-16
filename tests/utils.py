from datetime import datetime


def insert_appointment(
    session, since: datetime, until: datetime, accepted: bool
) -> None:
    session.execute(
        "INSERT INTO appointments (since, until, accepted) "
        "VALUES (:since, :until, :accepted)",
        {"since": since, "until": until, "accepted": accepted},
    )
    session.commit()
