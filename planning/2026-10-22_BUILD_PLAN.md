# Flyte 2 + hosted open-model build plan

## Goal

By tonight, have a working way to use Flyte 2 to manage LLM calls to an
open-weight model hosted by Fireworks or Together AI.

## Success criteria

- One direct API call to the selected provider succeeds.
- The response, latency, token usage, and errors can be captured.
- A simple Flyte 2 task runs successfully.
- Flyte runs the known-working provider call.
- Several prompts can run concurrently.
- Results are written to `work/results/open_model_experiment.json`.

## Execution plan

1. Choose Fireworks or Together AI and identify a valid hosted model ID.
2. Configure the provider credential locally without committing it.
3. Make one direct API call outside Flyte.
4. Confirm the response, latency, token usage, and error handling.
5. Start or verify the local Flyte 2 devbox and UI.
6. Run a minimal Flyte task that does not call the model provider.
7. Put the already-working provider call inside a Flyte task.
8. Run several prompts concurrently and collect structured results.
9. Verify `work/results/open_model_experiment.json` and inspect the run in the Flyte UI.
10. Add evaluation loops only after the end-to-end path is reliable.

## Permission checkpoints

Before proceeding, ask for explicit approval to:

- Build or rebuild a container image.
- Start, stop, or modify containers or the Flyte devbox.
- Launch a Flyte run.
- Make a real provider API call.
- Install or upgrade dependencies.

Reading files, explaining the next step, and editing this plan do not require
an execution approval.
