# User Guide (English)

This guide is for first-time users who want to run the project step by step.

## 1. What you get

After setup, you will be able to:

- open the browser UI
- fill in a guided workflow
- preview PLAN.md before generating AGENTS.md
- review results and generated cases
- optionally enable or disable model enhancement

## 2. Requirements

- Python 3.10 or newer
- a terminal
- a modern browser

## 3. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional environment file:

```bash
cp .env.example .env
```

Use `.env` only if you want admin-protected model configuration or a default model runtime.

## 4. Run

```bash
set -a
[ -f ./.env ] && . ./.env
set +a
agents-corpus serve-api --source-root . --output-dir ./tmp --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

## 5. First-run expectations

These are normal on first launch:

- empty case library
- empty results page
- model enhancement disabled or unconfigured

You can still start from the Create page immediately.

## 6. Optional model setup

- If you want system-default model mode, set:
  - `OPENAI_BASE_URL`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
- If you want to save settings from the UI, set:
  - `AGENTS_ADMIN_TOKEN`

Without `AGENTS_ADMIN_TOKEN`, the model configuration dialog is read-only.

## 7. Stop the service

Press `Ctrl+C` in the terminal running the server.

## 8. Next documents

- Filling guide: [`FILLING_GUIDE.en.md`](./FILLING_GUIDE.en.md)
- Deployment guide: [`../deployment/README.zh-CN.md`](../deployment/README.zh-CN.md)
