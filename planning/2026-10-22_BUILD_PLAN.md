# Flyte 2 + hosted open-model build plan

## Goal

By tonight, have a working way to use Flyte 2 to manage LLM calls to an
open-weight model hosted by Together AI.

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

## Progress on October 22, 2026

Completed:

- Selected Together AI and verified two hosted model IDs.
- Stored the local API key outside Git.
- Verified a direct Together API call with response, latency, token usage, and
  error handling.
- Verified the local Flyte devbox and UI.
- Ran a minimal Flyte task successfully.
- Created a Flyte-managed `together-api-key` secret and injected it only at task
  runtime.
- Ran one Together call from Flyte.
- Ran a parent task with two concurrent model-call child tasks and inspected all
  three actions in the Flyte UI.

Remaining for tonight:

- Build and verify the prepared two-model, three-prompt parent/child workflow.
- Capture response, latency, token usage, instruction checks, and errors for all
  six calls.
- Generate a readable parent comparison in the Flyte Reports tab.
- Write the aggregated result to `work/results/open_model_experiment.json`.
- Inspect and document the successful six-call run.

The Flyte Metrics tab is not a requirement for tonight. It generally depends on
infrastructure telemetry integration. Experiment measurements belong in the
Flyte report and JSON result.

## Permission checkpoints

Before proceeding, ask for explicit approval to:

- Build or rebuild a container image.
- Start, stop, or modify containers or the Flyte devbox.
- Launch a Flyte run.
- Make a real provider API call.
- Install or upgrade dependencies.

Reading files, explaining the next step, and editing this plan do not require
an execution approval.

## Public records

GitHub issues are the public record for decisions and completed implementation
steps. See the issue index in `README.md`. Issue #4 tracks the final six-call
experiment.
