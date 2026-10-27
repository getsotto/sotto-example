# Maintaining the examples

Keep each example a small standard-library terminal program. All nine must:

- Read `DEMO_SECRET` from the process environment without a Sotto SDK.
- Reject an absent or empty value with exit code `1` and the documented stderr message.
- Accept any non-empty value (including `0`) with exit code `0` and the documented stdout message.
- Never print the value, a prefix, or a hash of it.

## Checks

Run the checker's standard-library regression tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

These tests require only Python and check exact output validation, including
the known `exit status 1` trailer from `go run`. Unexpected child output is
rejected without being printed in failure diagnostics.

With all listed runtimes and CMake installed, run from the repository root:

```sh
python3 scripts/check_examples.py
```

On Windows use `py -3` in place of `python3`. To check only installed languages:

```sh
python3 scripts/check_examples.py python javascript typescript java go rust
```

The repository's maintenance workflow checks all nine languages on macOS,
Linux, and Windows with synthetic environment values. A separate Linux job
checks the real `sotto` local flow (`status`, `init`, `env`, `set`, `ls`, `run`,
`import`, and `lock`/`unlock`) with a disposable OS keyring.
It uses no hosted account or repository secrets. This is validation for these
examples; user-facing CI integration belongs in
[sotto-action](https://github.com/getsotto/sotto-action).

Do not run the Sotto integration check in a personal keychain. Overriding
`SOTTO_DATA_DIR` isolates the store but does not isolate Sotto's keychain entries.

## README animation

The GIF is an illustrated terminal walkthrough, not a raw terminal recording.
It summarises first-run prompts and contains no actual Emergency Kit or secrets.
The readable README steps are its text equivalent.

To regenerate it, install Pillow in a temporary virtual environment and run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install Pillow
.venv/bin/python scripts/render_demo.py
```

On Windows use `.venv\Scripts\python.exe` for the last two commands. The renderer
uses a system monospace font when available and falls back to Pillow's bundled font.

If CLI behavior changes, update the walkthrough and the animation together.
