from typing import Dict, Any, List

from timetable.service_layer.unit_of_work import AbstractUnitOfWork


def list_appointments(
    of_user: str, for_user: str, uow: AbstractUnitOfWork
) -> List[Dict[str, Any]]:
    with uow:
        c = uow.calendars.get(of_user)
        if for_user == of_user:
            apps = [a.to_dict() for a in c.list_appointments()]
        else:
            apps = [
                _mask(a.to_dict()) for a in c.list_appointments() if a.accepted
            ]
        return apps


def get_user(account_name: str, uow: AbstractUnitOfWork) -> Dict[str, Any]:
    with uow:
        u = uow.users.get(account_name)
        return u.to_dict()


def search_services(
    tags: List[str], uow: AbstractUnitOfWork
) -> List[Dict[str, Any]]:
    with uow:
        us = uow.users.list_services()
        for t in tags:
            us = [u for u in us if t in u.tags]
        us_masked = [_mask_service(u.to_dict()) for u in us]
        return us_masked


def get_appointment(
    account_name: str, id: int, uow: AbstractUnitOfWork
) -> Dict[str, Any]:
    with uow:
        c = uow.calendars.get(account_name)
        app = c.get_appointment(id)
        return app.to_dict()


def _mask_service(u: Dict[str, Any]) -> Dict[str, Any]:
    masked = dict()
    masked["account_name"] = u["account_name"]
    masked["tags"] = u["tags"]
    return masked


def _mask(app: Dict[str, Any]) -> Dict[str, str]:
    masked = dict()
    masked["since"] = app["since"]
    masked["until"] = app["until"]
    return masked
