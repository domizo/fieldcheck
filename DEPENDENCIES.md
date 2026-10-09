Runtime: Python standard library only; no pip install, lockfile, API account, key, or provider access is needed. Python 3.11+ is supported by the source; the local verification used Python 3.14.8. The CI matrix for 3.11 and 3.14 is configured but has not run remotely.

`pyproject.toml` records the zero-dependency runtime contract. Tests use `unittest`. Checksums use `hashlib`; JSON and CLI parsing use the standard library. A packaging backend is intentionally absent: run the module directly from this repository.

Optional development checks are isolated in a project virtual environment. `requirements-dev.lock` pins Ruff, mypy and their transitive dependencies, selected from the public PyPI registry. They are not imported by the runtime. Reproduce lint/type checks with:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/ruff check fieldcheck tests fixtures/make_negative_controls.py
.venv/bin/ruff format --check fieldcheck tests fixtures/make_negative_controls.py
.venv/bin/python -m mypy fieldcheck
```
