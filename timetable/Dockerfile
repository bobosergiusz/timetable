FROM python:3.8.5-buster

COPY requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

WORKDIR /src

COPY timetable /src/timetable
COPY pyproject.toml /src

RUN pip install .

ENV FLASK_APP=timetable.entrypoints.flask_app:flask_app
ENV FLASK_DEBUG=1
ENV PYTHONBUFFERED=1

COPY entrypoint.sh /
ENTRYPOINT [ "/entrypoint.sh" ]

CMD [ "flask", "run", "--host=0.0.0.0", "--port=80" ]