# Flyte 2 + hosted open-model experiment

This is the smallest useful experiment for tonight: Flyte runs three prompts in
parallel against either Fireworks AI or Together AI and writes the collected
responses to `work/results/open_model_experiment.json`.

## 1. Create the local environment

Use Python 3.12 if available. Docker must be running.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip flyte
flyte start devbox
flyte create config --devbox
```

If `flyte-devbox` is already running, do not start a second one. The project-local
`.flyte/config.yaml` points Flyte at the devbox and its local image registry.

## 2. Configure one provider

Fireworks:

```bash
export MODEL_PROVIDER=fireworks
export MODEL_BASE_URL=https://api.fireworks.ai/inference/v1
export MODEL_NAME=<a Fireworks model id>
export MODEL_API_KEY=<your Fireworks API key>
```

Together:

```bash
export MODEL_PROVIDER=together
export MODEL_BASE_URL=https://api.together.xyz/v1
export MODEL_NAME=<a Together model id>
export MODEL_API_KEY=<your Together API key>
```

Do not put the API key in this file or commit it.

## 3. Run the experiment

```bash
source .venv/bin/activate
python work/flyte_open_model_experiment.py
```

Open the Flyte URL printed by the script. The local result is written to
`work/results/open_model_experiment.json` after the run completes.

The launcher forwards the four `MODEL_*` variables to the Flyte task at run
time. They are not baked into the task image. For shared or production clusters,
replace the API-key environment variable with a Flyte-managed secret.

## What this demonstrates

- A Flyte 2 task calling an external OpenAI-compatible model API
- Parallel calls using ordinary Python `asyncio.gather`
- Per-prompt latency, usage, and error capture
- A durable Flyte run that can be inspected in the UI

It deliberately does not include fine-tuning, web scraping, S3, or a judge model.
Those are the next layers after this thin vertical slice works.
