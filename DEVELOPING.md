## Development setup

The easiest way to get set up for development is to install Python `>=3.7` and [poetry](https://pypi.org/project/poetry/), and then run the following from the top-level project directory:

```bash
  poetry install
  poetry shell
```

## Development commands

There are various makefile commands that help the development. Some of them are:

- To run lint checks:

  ```bash
    pylint
  ```

- To run tests:

  ```bash
    pytest
  ```

Before committing and opening a PR, use the above commands to run the checks locally. This saves CI hours and ensures you only commit clean code.