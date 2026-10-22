# Flyte 2 + Together AI experiment

This project incrementally proves a local Flyte 2 workflow for comparing hosted
open-weight models through Together AI.

## Safety rules

- Never commit `.env` or an API key.
- Never copy `.env` into an image.
- Never pass `MODEL_API_KEY` as a task input, build argument, or ordinary Flyte
  run environment value.
- Store the key in Flyte and inject it only into model-calling task containers.
- Get explicit approval before builds, Flyte runs, provider calls, dependency
  installations, or other potentially lengthy or cost-bearing operations.

## 1. Direct API smoke test

For direct local development, load the ignored `.env` into the current shell:

```bash
set -a
source .env
set +a
```

Then run:

```bash
.venv/bin/python work/together_api_smoke_test.py
```

This path is outside Flyte and reads `MODEL_API_KEY` from the local process
environment.

## 2. Verify the local Flyte devbox

Check its state:

```bash
.venv/bin/flyte get devbox
```

Start or resume it only when needed:

```bash
.venv/bin/flyte start devbox
```

The local UI is available at <http://localhost:30080/v2/projects> while the
devbox is running.

## 3. Store the Together key in Flyte

Create the secret interactively so the value is not placed in shell history:

```bash
.venv/bin/flyte \
  --config .flyte/config.yaml \
  create secret together-api-key \
  --project flytesnacks \
  --domain development
```

Verify its existence without displaying its value:

```bash
.venv/bin/flyte \
  --config .flyte/config.yaml \
  get secret together-api-key \
  --project flytesnacks \
  --domain development
```

In Flyte 2.12.1, the task environment requests the secret:

```python
model_env = flyte.TaskEnvironment(
    name="together_model_call",
    image=image,
    secrets=flyte.Secret(
        "together-api-key",
        as_env_var="MODEL_API_KEY",
    ),
)
```

The image contains code and dependencies. Flyte injects the key into the running
container as `MODEL_API_KEY`; the key is not part of the image.

## 4. Verified Flyte steps

Minimal Flyte task:

```bash
.venv/bin/flyte build work work/flyte_smoke_test.py env
.venv/bin/python work/flyte_smoke_test.py
```

One Together call from Flyte:

```bash
.venv/bin/flyte build work work/flyte_together_smoke_test.py env
.venv/bin/python work/flyte_together_smoke_test.py
```

The parent/child pattern was verified with two child calls:

```bash
.venv/bin/flyte build \
  work \
  work/flyte_two_model_comparison.py \
  comparison_env

.venv/bin/python work/flyte_two_model_comparison.py
```

The comparison creates one parent orchestration action and two concurrently
executing child model-call actions. Inside the parent, `call_model` is a Flyte
task object created by `@model_env.task`; its `.aio()` method submits an
asynchronous child action.

## 5. Final local milestone (completed)

The report-enabled expansion of the parent/child pattern was built, run, and
verified (run `rhlhkckxv6fcsn4q2984`, issue #8):

```text
2 models × 3 prompts = 6 child model calls
```

The six-call workflow has its own entry point so the verified two-child step
remains unchanged:

```bash
.venv/bin/flyte build \
  work \
  work/flyte_six_call_experiment.py \
  experiment_env

.venv/bin/python work/flyte_six_call_experiment.py
```

The parent:

- collects response, latency, usage, instruction checks, and errors;
- generates a readable comparison in the Flyte Reports tab; and
- writes the full result to `work/results/open_model_experiment.json` from the
  local launcher after the run finishes.

Use the run graph for concurrency and lineage, Summary for raw inputs and
outputs, Logs for debugging, and Reports for the human-readable experiment
comparison. The Metrics tab is infrastructure-oriented and is not required for
the local experiment.

## Legacy prototype

`work/flyte_open_model_experiment.py` is an earlier prototype. It runs multiple
HTTP calls inside one Flyte task, forwards the API key as an ordinary run
environment value, and uses an obsolete result accessor. Do not use it as the
basis for the final workflow.

Public decisions and implementation records are linked from `README.md`.
