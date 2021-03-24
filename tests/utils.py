from datetime import datetime
from typing import List


def insert_appointment(
    session, since: datetime, until: datetime, accepted: bool
) -> None:
    session.execute(
        "INSERT INTO appointments (since, until, accepted) "
        "VALUES (:since, :until, :accepted)",
        {"since": since, "until": until, "accepted": accepted},
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
