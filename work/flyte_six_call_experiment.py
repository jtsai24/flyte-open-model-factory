"""Compare two Together-hosted models across three prompts with Flyte."""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import time
from pathlib import Path

import flyte
import flyte.report


image = flyte.Image.from_debian_base(python_version=(3, 12)).with_pip_packages(
    "together==3.0.0",
)

model_env = flyte.TaskEnvironment(
    name="six_call_model",
    image=image,
    secrets=flyte.Secret(
        "together-api-key",
        as_env_var="MODEL_API_KEY",
    ),
)

experiment_env = flyte.TaskEnvironment(
    name="six_call_experiment",
    image=image,
    depends_on=[model_env],
)


def _instruction_check(prompt_id: str, response: str | None) -> tuple[bool, str]:
    if not response:
        return False, "Response is empty"
    if prompt_id == "three_sentences":
        sentence_count = len(re.findall(r"[.!?]+(?:\s|$)", response.strip()))
        return sentence_count == 3, f"Found {sentence_count} sentence endings; expected 3"
    if prompt_id == "three_bullets":
        bullet_count = len(
            re.findall(r"^\s*(?:[-*•]|\d+[.)])\s+", response, flags=re.MULTILINE)
        )
        return bullet_count == 3, f"Found {bullet_count} bullets; expected 3"
    return True, "Response is nonempty; review its usefulness manually"


def _child_report(result: dict[str, object]) -> str:
    response = html.escape(str(result.get("response") or ""))
    error = html.escape(str(result.get("error") or ""))
    return f"""
    <h2>Model call</h2>
    <table>
      <tr><th>Requested model</th><td>{html.escape(str(result["model"]))}</td></tr>
      <tr><th>Response model</th><td>{html.escape(str(result["response_model"]))}</td></tr>
      <tr><th>Prompt ID</th><td>{html.escape(str(result["prompt_id"]))}</td></tr>
      <tr><th>Latency</th><td>{result["latency_seconds"]} seconds</td></tr>
      <tr><th>Prompt tokens</th><td>{result["prompt_tokens"]}</td></tr>
      <tr><th>Completion tokens</th><td>{result["completion_tokens"]}</td></tr>
      <tr><th>Total tokens</th><td>{result["total_tokens"]}</td></tr>
      <tr><th>Finish reason</th><td>{html.escape(str(result["finish_reason"]))}</td></tr>
      <tr><th>Instruction check</th><td>{result["instruction_check_passed"]}: {html.escape(str(result["instruction_check_detail"]))}</td></tr>
      <tr><th>Error</th><td>{error or "None"}</td></tr>
    </table>
    <h3>Prompt</h3>
    <pre style="white-space:pre-wrap">{html.escape(str(result["prompt"]))}</pre>
    <h3>Response</h3>
    <pre style="white-space:pre-wrap">{response}</pre>
    """


@model_env.task(report=True)
def call_model(prompt_id: str, prompt: str, model: str) -> str:
    from together import Together

    started = time.perf_counter()
    try:
        response = Together(
            api_key=os.environ["MODEL_API_KEY"]
        ).chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = response.usage
        answer = response.choices[0].message.content or ""
        check_passed, check_detail = _instruction_check(prompt_id, answer)
        result = {
            "model": model,
            "response_model": response.model,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "response": answer,
            "latency_seconds": round(time.perf_counter() - started, 3),
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "finish_reason": response.choices[0].finish_reason,
            "instruction_check_passed": check_passed,
            "instruction_check_detail": check_detail,
            "error": None,
        }
    except Exception as error:
        result = {
            "model": model,
            "response_model": None,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "response": None,
            "latency_seconds": round(time.perf_counter() - started, 3),
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "finish_reason": None,
            "instruction_check_passed": False,
            "instruction_check_detail": "Model call failed",
            "error": f"{type(error).__name__}: {error}",
        }

    flyte.report.log(_child_report(result))
    flyte.report.flush()
    return json.dumps(result)


def _model_summary(results: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for result in results:
        model = str(result["model"])
        current = summary.setdefault(
            model,
            {
                "successful_calls": 0,
                "average_latency_seconds": 0.0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "instruction_checks_passed": 0,
            },
        )
        if result["error"] is None:
            current["successful_calls"] = int(current["successful_calls"]) + 1
        if result["instruction_check_passed"]:
            current["instruction_checks_passed"] = int(
                current["instruction_checks_passed"]
            ) + 1
        current["average_latency_seconds"] = float(
            current["average_latency_seconds"]
        ) + float(result["latency_seconds"])
        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
            current[field] = int(current[field]) + int(result[field] or 0)

    for current in summary.values():
        current["average_latency_seconds"] = round(
            float(current["average_latency_seconds"]) / 3,
            3,
        )
    return summary


def _overview_report(summary: dict[str, dict[str, object]]) -> str:
    rows = "".join(
        f"""
        <tr>
          <td>{html.escape(model)}</td>
          <td>{values["successful_calls"]}/3</td>
          <td>{values["average_latency_seconds"]}</td>
          <td>{values["prompt_tokens"]}</td>
          <td>{values["completion_tokens"]}</td>
          <td>{values["total_tokens"]}</td>
          <td>{values["instruction_checks_passed"]}/3</td>
        </tr>
        """
        for model, values in summary.items()
    )
    return f"""
    <h2>Two-model, three-prompt comparison</h2>
    <p>Use operational measurements together with human review of the responses. Lower latency or fewer tokens alone does not establish better model quality.</p>
    <table>
      <thead><tr><th>Model</th><th>Successes</th><th>Avg latency (s)</th><th>Prompt tokens</th><th>Completion tokens</th><th>Total tokens</th><th>Checks passed</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """


def _responses_report(
    prompt_ids: list[str],
    prompts: list[str],
    models: list[str],
    results: list[dict[str, object]],
) -> str:
    by_key = {(result["prompt_id"], result["model"]): result for result in results}
    sections = []
    for prompt_id, prompt in zip(prompt_ids, prompts):
        cells = []
        for model in models:
            result = by_key[(prompt_id, model)]
            response = html.escape(str(result["response"] or ""))
            error = html.escape(str(result["error"] or ""))
            cells.append(
                f"""
                <td style="vertical-align:top;width:50%">
                  <h4>{html.escape(model)}</h4>
                  <p><b>Latency:</b> {result["latency_seconds"]}s &nbsp; <b>Tokens:</b> {result["total_tokens"]}</p>
                  <p><b>Check:</b> {result["instruction_check_passed"]} — {html.escape(str(result["instruction_check_detail"]))}</p>
                  {f'<p style="color:#b42318"><b>Error:</b> {error}</p>' if error else ''}
                  <pre style="white-space:pre-wrap">{response}</pre>
                </td>
                """
            )
        sections.append(
            f"""
            <h3>{html.escape(prompt_id)}</h3>
            <p>{html.escape(prompt)}</p>
            <table><tr>{''.join(cells)}</tr></table>
            """
        )
    return "".join(sections)


def _details_report(results: list[dict[str, object]]) -> str:
    rows = "".join(
        f"""
        <tr>
          <td>{html.escape(str(result["prompt_id"]))}</td>
          <td>{html.escape(str(result["model"]))}</td>
          <td>{"Success" if result["error"] is None else "Error"}</td>
          <td>{result["latency_seconds"]}</td>
          <td>{result["prompt_tokens"]}</td>
          <td>{result["completion_tokens"]}</td>
          <td>{result["total_tokens"]}</td>
          <td>{html.escape(str(result["finish_reason"]))}</td>
          <td>{result["instruction_check_passed"]}</td>
          <td>{html.escape(str(result["error"] or ""))}</td>
        </tr>
        """
        for result in results
    )
    return f"""
    <h2>All model calls</h2>
    <table>
      <thead><tr><th>Prompt</th><th>Model</th><th>Status</th><th>Latency (s)</th><th>Prompt tokens</th><th>Completion tokens</th><th>Total tokens</th><th>Finish reason</th><th>Check</th><th>Error</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """


@experiment_env.task(report=True)
async def compare_models(
    prompt_ids: list[str],
    prompts: list[str],
    models: list[str],
) -> str:
    child_results = await asyncio.gather(
        *(
            call_model.aio(prompt_id=prompt_id, prompt=prompt, model=model)
            for prompt_id, prompt in zip(prompt_ids, prompts)
            for model in models
        )
    )
    results = [json.loads(result) for result in child_results]
    summary = _model_summary(results)

    flyte.report.get_tab("Overview").log(_overview_report(summary))
    flyte.report.get_tab("Responses").log(
        _responses_report(prompt_ids, prompts, models, results)
    )
    flyte.report.get_tab("Call details").log(_details_report(results))
    flyte.report.flush()

    return json.dumps({"summary": summary, "results": results})


if __name__ == "__main__":
    prompt_ids = ["three_sentences", "three_bullets", "hosting_difference"]
    prompts = [
        "Explain what a durable workflow runtime does in three concise sentences.",
        "Return exactly three bullet points describing when to fine-tune an open model.",
        "Give one practical difference between an API-hosted open model and self-hosting.",
    ]
    models = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "openai/gpt-oss-120b",
    ]

    flyte.init_from_config(".flyte/config.yaml")
    run = flyte.run(
        compare_models,
        prompt_ids=prompt_ids,
        prompts=prompts,
        models=models,
    )

    print(f"Flyte run: {run.name}")
    print(f"Flyte URL: {run.url}")
    run.wait()

    output = json.loads(run.outputs()[0])
    output["run_name"] = run.name
    output_path = Path("work/results/open_model_experiment.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Saved results to {output_path}")
