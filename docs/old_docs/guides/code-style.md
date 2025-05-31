# Code Style Guide

## Python

* Always use type hints for function parameters and return values.
* Always use type hints for variables.
* Use **Pydantic 2.0**.
* Use **`uv`** with `pyproject.toml` for dependency management.
* Place **all imports at the top** of the file.
* **Never** use `monkeypatch` or `@patch`; use DI instead.
* Always activate the virtual environment before running any Python command.

## TypeScript

* Do not use the `any` type.
* Use **`pnpm`** with `tsconfig.json` for dependency management.
* Use **Vitest** with **jsdom** for testing.
* Use **React Query** for data fetching.
* Use **React Testing Library** for UI testing.

# General

* Clear, descriptive naming.
* Modular, maintainable structure.
* Treat warnings as errors.
* Use the latest **stable** versions of dependencies, tools, and frameworks.
* Always check and understand the latest documentation.
* **DO NOT WRITE COMMENTS**.
* **DO NOT WRITE DOCSTRINGS**.

  * If you think you need them, **rewrite the code to be self-explanatory instead**.
