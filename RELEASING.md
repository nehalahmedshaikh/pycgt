# Releasing

## Before tagging

Run every check in [`CONTRIBUTING.md`](CONTRIBUTING.md). The commands below
assume a POSIX shell; cut releases from Linux or macOS.

Bump `version` in `pyproject.toml`, move the `Unreleased` heading in
`CHANGELOG.md` down to the new version, and date it.

On Windows, edit those files with something that writes UTF-8 **without** a
BOM. Windows PowerShell 5.1's `Set-Content -Encoding utf8` adds one, and a BOM
at the start of `pyproject.toml` makes every TOML parser reject the file with
`Invalid statement (at line 1, column 1)`.

## Build and verify

```console
$ python -m pip install --upgrade build twine
$ rm -rf dist build
$ python -m build
$ python -m twine check dist/*
```

`twine check` validates the metadata and confirms the README renders on PyPI.
It does **not** confirm the package works, so also install the built wheel into
a throwaway environment and exercise it from outside the source tree:

```console
$ python -m venv /tmp/verify
$ /tmp/verify/bin/pip install dist/pycgt-*.whl
$ cd /tmp && /tmp/verify/bin/python -c "
import pycgt, pathlib
from pycgt.rulesets import domineering
assert 'site-packages' in pycgt.__file__
assert (pathlib.Path(pycgt.__file__).parent / 'py.typed').exists()
print(pycgt.render(domineering.rectangle(2, 4)))   # Miny(2)
"
```

Running from the source directory would import the local `src/` copy and prove
nothing about the artifact.

## Uploading

**Never put the API token in a tracked file, a commit, or a chat.** The
username is the literal string `__token__`; the password is the token,
including its `pypi-` prefix.

Do a dry run on TestPyPI first — it is free, it exercises the whole pipeline,
and it does not consume the real version number. TestPyPI needs its own
account and its own token.

```console
$ python -m twine upload --repository testpypi dist/*
$ python -m pip install --index-url https://test.pypi.org/simple/ --no-deps pycgt
```

Then the real thing:

```console
$ python -m twine upload dist/*
```

Twine prompts for credentials, so nothing has to be stored anywhere. If you
would rather not be prompted, set them for the session only:

```console
$ export TWINE_USERNAME=__token__
$ export TWINE_PASSWORD=pypi-...        # PowerShell: $env:TWINE_PASSWORD="pypi-..."
```

For a persistent setup use `~/.pypirc`, readable only by you (`chmod 600`):

```ini
[pypi]
  username = __token__
  password = pypi-...
```

Scope the token to this project once the project exists on PyPI; the first
upload needs an account-wide token because the project is not there yet.

## After uploading

A version on PyPI can be *yanked* (hidden from resolution) but never replaced
or re-uploaded; fixes require a new version.

```console
$ git tag -a vX.Y.Z -m "vX.Y.Z"
$ git push origin vX.Y.Z
$ gh release create vX.Y.Z --generate-notes dist/*
```

Set the repository homepage to the PyPI page once it is live:

```console
$ gh repo edit --homepage "https://pypi.org/project/pycgt/"
```
