# Contribution guidelines

## Development

This project uses [tox](https://tox.wiki) for development tasks. You can install tox on macOS via Homebrew, in an all-purpose virtual environment, or with [pipx](https://pypa.github.io/pipx/).

### Running tests

Tests are the default task for tox. You can run the tests, complete with test coverage reporting, using the following command:

```shell
$ tox
```

### Running type checking

This project uses type hints and mypy for static type analysis. You can check the type agreement for the project using the following command:

```shell
$ tox -e typecheck
```

### Formatting code

This project uses [black](https://black.readthedocs.io/en/stable/) for code formatting. You can check the formatting of the code with the following command:

```
$ tox -e format
```

You can automatically reformat a file or directory by supplying it as a positional argument:

```
$ tox -e format src
```
