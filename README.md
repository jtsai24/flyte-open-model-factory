# Flyte Open Model Factory

Workspace for experimenting with Flyte 2 and hosted open-weight model APIs.

## Current goal

- Run Together AI inference calls as independently visible Flyte child tasks.
- Compare two hosted open-weight models over the same prompt set.
- Collect responses, latency, usage, and errors.
- Review the comparison in the Flyte UI and save the results as JSON.
- Add evaluation, fine-tuning, and cloud deployment now that the local workflow works.

## Verified so far

- Direct Together API access from the local virtual environment.
- A minimal task running on the local Flyte devbox.
- Secure API-key injection through a Flyte-managed secret.
- One Together model call from a Flyte task.
- One parent task concurrently running two child model-call tasks.
- A report-enabled six-call experiment (two models × three prompts): run
  `rhlhkckxv6fcsn4q2984` completed in 10.24 seconds with seven actions (one
  parent, six concurrent children) and no model-call errors. The Overview,
  Responses, and Call details report tabs rendered, and the aggregated result
  was written to `work/results/open_model_experiment.json`. See
  [#8](https://github.com/jtsai24/flyte-open-model-factory/issues/8) for the
  implementation walkthrough, comparison table, and screenshots.

The local milestone is complete. The next work is the evaluation baseline in
stage 1 of `planning/2026-10-22_EXPANSION_PLAN.md`.

## Current entry points

- `work/together_api_smoke_test.py`: direct Together API smoke test outside Flyte.
- `work/flyte_smoke_test.py`: minimal local Flyte task.
- `work/flyte_together_smoke_test.py`: one secret-backed Together call in Flyte.
- `work/flyte_two_model_comparison.py`: the verified one-prompt, two-child
  comparison.
- `work/flyte_six_call_experiment.py`: the verified six-call experiment with
  Flyte reports and local JSON output.
- `docs/FLYTE_2_LOCAL_GUIDE.md`: how to operate local Flyte 2 for this project.

`work/flyte_open_model_experiment.py` is an earlier prototype. It forwards the API
key as an ordinary run environment value and should not be used as the basis for
the final workflow.

## Public decision and implementation records

- [#1 Choose Together AI as the hosted open-weight model provider](https://github.com/jtsai24/flyte-open-model-factory/issues/1)
- [#2 Choose the initial hosted model](https://github.com/jtsai24/flyte-open-model-factory/issues/2)
- [#3 Connect to Together AI safely for a direct smoke test](https://github.com/jtsai24/flyte-open-model-factory/issues/3)
- [#4 Run the two-model, three-prompt Flyte experiment](https://github.com/jtsai24/flyte-open-model-factory/issues/4)
- [#5 Verify one task in the local Flyte UI](https://github.com/jtsai24/flyte-open-model-factory/issues/5)
- [#6 Inject the Together API key with a Flyte-managed secret](https://github.com/jtsai24/flyte-open-model-factory/issues/6)
- [#7 Validate parent/child fan-out with two models](https://github.com/jtsai24/flyte-open-model-factory/issues/7)
- [#8 Run the report-enabled six-call experiment](https://github.com/jtsai24/flyte-open-model-factory/issues/8)

See `planning/2026-10-22_BUILD_PLAN.md` for the local execution plan and
`planning/2026-10-22_EXPANSION_PLAN.md` for later phases.
