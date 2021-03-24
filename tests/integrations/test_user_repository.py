import pytest

from timetable.adapters.repository import DoesNotExistsError, SqlUserRepository
from timetable.domain.user import Client, Service

from tests.utils import insert_client, insert_service


def test_repository_can_add_client(Session):
    session = Session()
    u = Client(account_name="bob123", email="bob123@test.com", password="123")

    repository = SqlUserRepository(session)
    repository.add(u)
    session.commit()

    [[account_name, email, password]] = session.execute(
        "SELECT account_name, email, password FROM users"
    )

    assert account_name == u.account_name
    assert email == u.email
    assert password == u.password

    [[account_name]] = session.execute("SELECT account_name FROM clients")

    assert account_name == u.account_name


def test_repository_can_add_service_user(Session):
    session = Session()
    u = Service(
        account_name="bob123",
        email="bob123@test.com",
        password="123",
        tags=["Warsaw", "Mechanic"],
    )

    repository = SqlUserRepository(session)
    repository.add(u)
    session.commit()

    [[account_name, email, password]] = session.execute(
        "SELECT account_name, email, password FROM users"
    )
    [[type]] = session.execute("SELECT type FROM users")
    assert account_name == u.account_name
    assert email == u.email
    assert password == u.password

    [[account_name]] = session.execute("SELECT account_name FROM services")

    assert account_name == u.account_name

    [
        [service_account_name_1, tag_1],
        [service_account_name_2, tag_2],
    ] = session.execute("SELECT service_account_name, tag FROM tags")

    assert service_account_name_1 == u.account_name
    assert service_account_name_2 == u.account_name
    assert [tag_1, tag_2] == u.tags


def test_repository_can_get_client_by_existing_account_name(Session):
    session = Session()

    insert_client(session, "bob", "bob@dot.com", "123")
    repository = SqlUserRepository(session)
    u = repository.get("bob")

    assert u.account_name == "bob"
    assert u.email == "bob@dot.com"
    assert u.password == "123"


def test_repository_can_get_service_by_existing_account_name(Session):
    session = Session()

    insert_service(
        session, "bob", "bob@dot.com", "123", ["warsaw", "mechanic"]
    )
    repository = SqlUserRepository(session)
    u = repository.get("bob")

    assert u.account_name == "bob"
    assert u.email == "bob@dot.com"
    assert u.password == "123"
    assert u.tags == ["warsaw", "mechanic"]


def test_repository_cannot_get_by_nonexisting_id(Session):
    session = Session()
    repository = SqlUserRepository(session)
    with pytest.raises(DoesNotExistsError):
        insert_client(session, "john", "john@dot.com", "123")
        insert_service(
            session, "bob", "bob@dot.com", "123", ["warsaw", "mechanic"]
        )
        repository.get("sam")


def test_repository_can_list(Session):
    session = Session()
    insert_client(session, "john", "john@dot.com", "123")
    insert_service(
        session, "bob", "bob@dot.com", "123", ["warsaw", "mechanic"]
    )
    repository = SqlUserRepository(session)
    [u1, u2] = repository.list()

    assert u1.account_name == "john"
    assert u1.email == "john@dot.com"
    assert u1.password == "123"

    assert u2.account_name == "bob"
    assert u2.email == "bob@dot.com"
    assert u2.password == "123"
    assert u2.tags == ["warsaw", "mechanic"]
