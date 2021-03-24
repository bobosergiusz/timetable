import os


def get_database_uri():
    user = os.environ.get("PG_USER")
    password = os.environ.get("PG_PASSWORD")
    host = os.environ.get("PG_HOST")
    port = os.environ.get("PG_PORT")
    database = os.environ.get("PG_DATABASE")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def get_secret_key():
    return os.urandom(16)