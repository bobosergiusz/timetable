class NotAvailableError(BaseException):
    """There is appointment during this time"""


class DoesNotExistsError(BaseException):
    """No such appointment"""
