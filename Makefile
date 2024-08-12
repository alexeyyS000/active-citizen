SRC_DIR=src

LOCALE_DIR=$(SRC_DIR)/locale
LOCALE_CONFIG=$(LOCALE_DIR)/babel.cfg
MESSAGE_DOMAIN=messages
MESSAGE_DOMAIN_FILE=$(LOCALE_DIR)/$(MESSAGE_DOMAIN).pot

locale-init:
	poetry run pybabel init --output-dir=$(LOCALE_DIR) --locale=$(locale) --no-wrap

locale-new:
	poetry run pybabel init --input-file=$(MESSAGE_DOMAIN_FILE) --output-dir=$(LOCALE_DIR) --locale=$(locale) --no-wrap

locale-compile:
	poetry run pybabel compile --domain=$(MESSAGE_DOMAIN) --use-fuzzy --directory=$(LOCALE_DIR)

locale-update:
	poetry run pybabel update --domain=$(MESSAGE_DOMAIN) --input-file=$(MESSAGE_DOMAIN_FILE) --output-dir=$(LOCALE_DIR) --no-wrap

locale-template:
	poetry run pybabel extract --mapping-file=$(LOCALE_CONFIG) --output-file=$(MESSAGE_DOMAIN_FILE) --no-wrap .

mypy:
	poetry run mypy --config formatters-cfg.toml $(SRC_DIR)

flake:
	poetry run flake8 --toml-config formatters-cfg.toml $(SRC_DIR)

black:
	poetry run black --config formatters-cfg.toml $(SRC_DIR)

black-lint:
	poetry run black --check --config formatters-cfg.toml $(SRC_DIR)

isort:
	poetry run isort --settings-path formatters-cfg.toml $(SRC_DIR)

format: black isort

lint: flake mypy black-lint

test:
	poetry run pytest --test-alembic -n logical --reruns 3 $(SRC_DIR)

install:
	poetry install --no-root

develop:
	docker compose up redis db minio -d

build:
	docker compose build

down:
	docker compose down

lock:
	poetry lock --no-update
