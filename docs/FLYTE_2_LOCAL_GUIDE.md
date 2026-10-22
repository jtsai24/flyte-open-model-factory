# Working with Flyte 2 locally

This guide summarizes the Flyte 2 workflow verified in this repository.

## Mental model

```text
Python launcher
    ↓
Flyte services in the local devbox
    ↓
Kubernetes task containers on this laptop
    ↓
Together AI hosted model API
```

The container image contains code and dependencies. Secrets are injected only
when Kubernetes starts a task container.

## Check the local setup

Run commands from the repository root.

```bash
.venv/bin/flyte --version
.venv/bin/flyte get devbox
docker ps --filter name=flyte-devbox
```

The project configuration is `.flyte/config.yaml`. The local UI is available at
<http://localhost:30080/v2/projects> while the devbox is running.

## Start and stop the devbox

Start or resume it:

```bash
.venv/bin/flyte start devbox
```

Stop or pause it when finished:

```bash
.venv/bin/flyte stop devbox
```

Stopping the devbox pauses its container and preserves local Flyte state. Confirm
the result with:

```bash
docker ps --filter name=flyte-devbox
```

## Store an API key safely

Create the Together secret interactively:

```bash
.venv/bin/flyte \
  --config .flyte/config.yaml \
  create secret together-api-key \
  --project flytesnacks \
  --domain development
```

Do not use `--value`; a command-line value can remain in shell history.

Verify that the secret exists without displaying its value:

```bash
.venv/bin/flyte \
  --config .flyte/config.yaml \
  get secret together-api-key \
  --project flytesnacks \
  --domain development
```

Never put an API key in Git, an image, a task input, a build argument, or an
ordinary Flyte run environment value.

## Define an image and task environment

```python
import flyte

image = flyte.Image.from_debian_base(python_version=(3, 12)).with_pip_packages(
    "together==3.0.0",
)

model_env = flyte.TaskEnvironment(
    name="model_call",
    image=image,
    secrets=flyte.Secret(
        "together-api-key",
        as_env_var="MODEL_API_KEY",
    ),
)
```

`TaskEnvironment` describes the image and runtime settings shared by its tasks.
In Flyte 2.12.1, secrets are declared on the environment.

## Define a task

```python
import os

@model_env.task
def call_model(prompt: str, model: str) -> str:
    api_key = os.environ["MODEL_API_KEY"]
    # Call Together and return the result.
```

The decorator replaces the ordinary function name with a Flyte task object.
Typed parameters become Flyte inputs, and the return annotation becomes the
Flyte output type.

## Fan out child tasks

Create a parent environment that depends on the model-calling environment:

```python
parent_env = flyte.TaskEnvironment(
    name="experiment",
    image=image,
    depends_on=[model_env],
)
```

Submit child actions concurrently from an asynchronous parent:

```python
import asyncio

@parent_env.task
async def compare(prompt: str, models: list[str]) -> list[str]:
    return await asyncio.gather(
        *(call_model.aio(prompt=prompt, model=model) for model in models)
    )
```

`.aio()` comes from the Flyte task object created by `@model_env.task`. Inside a
running parent task, it submits a child Flyte action and returns an awaitable for
the child output.

The parent normally runs in one pod, and each child action normally runs in its
own pod.

## Format output in Flyte Reports

Enable reporting on the task:

```python
@parent_env.task(report=True)
async def compare(...):
    ...
```

Write escaped HTML into named report tabs:

```python
import html
import flyte.report

safe_response = html.escape(model_response)

flyte.report.get_tab("Overview").log("<h2>Experiment overview</h2>")
flyte.report.get_tab("Responses").log(
    f'<pre style="white-space:pre-wrap">{safe_response}</pre>'
)
flyte.report.flush()
```

Always escape prompts, responses, errors, and other untrusted text before
inserting them into HTML.

Use the UI tabs for different purposes:

- **Summary:** raw inputs and outputs
- **Logs:** debugging output
- **Reports:** human-readable experiment comparisons
- **Metrics:** infrastructure telemetry when a metrics backend is configured

## Build an environment image

The command format is:

```text
flyte build <source root> <Python file> <environment variable>
```

For the six-call experiment:

```bash
.venv/bin/flyte build \
  work \
  work/flyte_six_call_experiment.py \
  experiment_env
```

The final `experiment_env` is the Python variable name of the environment to
build. Its `depends_on` relationship includes the child environment.

Rebuild when image dependencies or task code change. A change only to local
launcher output handling may not require rebuilding.

## Submit a Flyte run

Run the Python launcher:

```bash
.venv/bin/python work/flyte_six_call_experiment.py
```

This submits the parent task. Flyte starts the necessary task containers. For
this experiment, it also makes six billable Together API calls.

The launcher prints the run ID and Flyte UI URL, waits for completion, reads the
result with `run.outputs()[0]`, and writes:

```text
work/results/open_model_experiment.json
```

Generated experiment results are ignored by Git.

## Inspect a run

Use the printed UI URL to inspect the parent, children, inputs, outputs, logs,
timelines, and reports.

Useful read-only CLI commands include:

```bash
.venv/bin/flyte --config .flyte/config.yaml get run <run-id>
.venv/bin/flyte --config .flyte/config.yaml get action <run-id>
.venv/bin/flyte --config .flyte/config.yaml get io <run-id>
```

## Common mistakes

- Use `.venv/bin/flyte` if `flyte` is not on `PATH`.
- Use `run.outputs()[0]`, not `run.result`, with Flyte 2.12.1.
- Put secrets on `TaskEnvironment`, not `@env.task`, in Flyte 2.12.1.
- Set `report=True`; otherwise task-generated report content is unavailable.
- Multiple HTTP calls inside one task remain one Flyte action. Use `.aio()` child
  tasks when each call should be visible independently.

## Shutdown checklist

1. Confirm that the run finished.
2. Review the Flyte report and saved JSON output.
3. Document important results in the relevant GitHub issue.
4. Stop the devbox:

```bash
.venv/bin/flyte stop devbox
```

Builds, Flyte runs, provider calls, dependency installations, and cloud changes
require an explanation and explicit approval before execution.
