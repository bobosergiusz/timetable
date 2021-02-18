build:
	docker-compose build

up:
	docker-compose up -d timetable

test: down up
	sleep 3 && docker-compose run e2e-tests

logs:
	docker-compose logs timetable | tail -100

down:
	docker-compose down --remove-orphans -v

all: down build up