up:
	docker compose up --build

down:
	docker compose down

test:
	.venv/bin/pytest

build:
	docker compose build
