# Contributing

Thank you for contributing to Agents Production Studio.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Common Commands

Run the local server:

```bash
make run
```

Run tests:

```bash
make test
```

Build a release archive:

```bash
make package
```

## Pull Request Expectations

- Keep changes focused and reviewable.
- Preserve the browser-first workflow.
- Do not introduce hard-coded local paths.
- Do not expose local corpora, tokens, logs, or private runtime data.
- If you change user-facing flows, update the docs in `docs/`.

## Documentation Expectations

Update documentation when you change:

- installation or startup behavior
- deployment behavior
- model configuration flows
- form fields or output expectations

## Tests

At minimum, run:

```bash
python -m unittest discover -s tests
```
