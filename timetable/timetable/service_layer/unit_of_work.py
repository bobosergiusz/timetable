from timetable.adapters.repository import SqlRepository


class SqlUnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.appointments = SqlRepository(self.session)
        return self

    def __exit__(self, type, value, traceback):
        self.rollback()

    def rollback(self):
        self.session.rollback()

    def commit(self):
        self.session.commit()
