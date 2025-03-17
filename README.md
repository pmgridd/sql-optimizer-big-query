# big-query-agent-optimizer

## Development Setup

* Install a local Python version (see `.python-version` 3.11.10)
  e.g. with pyenv: `pyenv install 3.11.10`, `pyenv global 3.11.10`
* Run `make dev-setup`

## Code quality

`make dev-setup` command defined in the `Makefile` is installing several automatic code quality
tools, configuration and definitions for which could be found in the `.pre-commit-config.yaml`
file.

Pre-commit hooks will be executed automatically on any invocation of the `git commit` command or
could manually be run via `make pre-commit`.

## Testing

Unit tests for the source code are located under `tests/src`, run

`make unit-tests`

in order to execute them with pytest.

## Dependency management

This project uses Pipenv for dependency management. To reinstall all dependencies
listed in the `Pipfile` execute:

```bash
pipenv install --dev
```

Note, that "[packages]" section contains the dependencies needed for the actual runtime
execution
of the code scheduling the pipelines or executing at pipeline runtime environment

"[dev-packages]" section contains the rest of the dependencies necessary to work with the
repository automation: code quality tools, unit test libraries, etc.

After installing or updating packages, please don't forget to commit the updated
lock file (`Pipfile.lock`) to the repository

```bash
pipenv lock
git add Pipfile.lock
```
