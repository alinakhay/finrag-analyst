.PHONY: install dev api test evaluate lint build docker full-up full-down

install:
	npm ci
	python -m pip install -e "./api[dev]"

dev:
	npm run dev

api:
	uvicorn app.main:app --app-dir api --reload --port 8000

test:
	pytest api/tests

evaluate:
	cd api && python -m evaluation.evaluate

lint:
	npm run lint
	ruff check api

build:
	npm run build

docker:
	docker build -t catalystlens .
	docker run --rm -p 8000:8000 catalystlens

full-up:
	docker compose up --build -d

full-down:
	docker compose down
