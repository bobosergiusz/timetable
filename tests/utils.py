from datetime import datetime
from typing import List


def insert_calendar(session, owner: str):
    session.execute(
        "INSERT INTO calendars (owner, id_count) " "VALUES (:owner, 0)",
        {"owner": owner},
    )
    session.commit()


def insert_appointment(
    session,
    owner: str,
    from_user: str,
    since: datetime,
    until: datetime,
    description: str,
    accepted: bool,
) -> None:
    [[id]] = session.execute(
        "SELECT IFNULL(max(id), 0) + 1 "
        "FROM appointments "
        "WHERE calendar_owner=:owner",
        {"owner": owner},
    )
    session.execute(
        "INSERT INTO appointments (calendar_owner, id, from_user, since, "
        "until, description, accepted) "
        "VALUES (:owner, :id, :from_user, :since, "
        ":until, :description, :accepted)",
        {
            "owner": owner,
            "id": id,
            "from_user": from_user,
            "since": since,
            "until": until,
            "description": description,
            "accepted": accepted,
        },
    )
    session.commit()


def insert_client(
    session, account_name: str, email: str, password: str
) -> None:
    session.execute(
        "INSERT INTO users (account_name, email, password, type) "
        "VALUES (:account_name, :email, :password, 'client')",
        {"account_name": account_name, "email": email, "password": password},
    )
    session.execute(
        "INSERT INTO clients (account_name) VALUES (:account_name)",
        {"account_name": account_name},
    )
    session.commit()


def insert_service(
    session, account_name: str, email: str, password: str, tags: List[str]
) -> None:
    session.execute(
        "INSERT INTO users (account_name, email, password, type) "
        "VALUES (:account_name, :email, :password, 'service')",
        {"account_name": account_name, "email": email, "password": password},
    )
    session.execute(
        "INSERT INTO services (account_name) VALUES (:account_name)",
        {"account_name": account_name},
    )
    for tag in tags:
        session.execute(
            "INSERT INTO tags (service_account_name, tag)"
            " VALUES (:account_name, :tag)",
            {"account_name": account_name, "tag": tag},
        )
    session.commit()
