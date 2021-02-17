FROM python:3.8.5-buster

RUN pip install requests pytest

COPY tests.py /tests/

WORKDIR /tests

ENTRYPOINT [ "bash", "-c" ]

CMD [ "pytest tests.py" ]