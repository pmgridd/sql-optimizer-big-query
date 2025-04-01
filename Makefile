export PIPENV_IGNORE_VIRTUALENVS := 1 ## Make sure pipenv uses it's own environment

help: ## Display this help screen
	@grep -h -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

pre-commit: ## Runs the pre-commit over entire repo
	@pipenv run pre-commit run --all-files

unit-tests: ## Runs unit tests
	@pipenv run python -m pytest

dev-setup: ## Installs the development environment and pre-commit hooks
	@pip install pipenv && \
	pipenv install --dev && \
	pipenv run pre-commit install  # Install pre-commit hooks

run-local:
	@pipenv run python -m src.main

run-local-streaming:
	@pipenv run python -m src.main_streaming_example

docker-build-local:
	@docker build -t sql-optimization-agents:latest -f docker/Dockerfile .

docker-run-local:
	@docker run -p 8880:8880 --env-file .env sql-optimization-agents:latest

dbl:
	@docker build -t sql-optimization-agents:latest -f docker/Dockerfile .

drl:
	@docker run -p 8880:8880 --env-file .env sql-optimization-agents:latest
