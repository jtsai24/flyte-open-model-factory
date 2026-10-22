"""Run a small Flyte 2 experiment against a hosted open-model API.

Supports Fireworks AI and Together AI because both expose an OpenAI-compatible
API. The task fans out over prompts, collects responses, and returns JSON-safe
results. The launcher writes the final result locally after the Flyte run.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import flyte


env = flyte.TaskEnvironment(
    name="open_model_experiment",
    image=flyte.Image.from_debian_base(python_version=(3, 12)).with_pip_packages(
        "openai>=1.0.0",
    ),
)


PROMPTS = [
    "Explain what a durable workflow runtime does in three concise sentences.",
    "Return exactly three bullet points describing when to fine-tune an open model.",
    "Give one practical difference between an API-hosted open model and self-hosting.",
]


async def _call_model(prompt: str) -> dict[str, object]:
    from openai import AsyncOpenAI

    started = time.perf_counter()
    provider = os.environ.get("MODEL_PROVIDER", "custom")
    model = os.environ["MODEL_NAME"]
    client = AsyncOpenAI(
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.environ["MODEL_BASE_URL"],
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )
        return {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "response": response.choices[0].message.content or "",
            "latency_seconds": round(time.perf_counter() - started, 3),
            "usage": response.usage.model_dump() if response.usage else None,
            "error": None,
        }
    except Exception as exc:  # Keep one failed prompt from losing the experiment.
        return {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "response": None,
            "latency_seconds": round(time.perf_counter() - started, 3),
            "usage": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


@env.task
async def run_experiment(prompts: list[str]) -> str:
    results = list(await asyncio.gather(*(_call_model(prompt) for prompt in prompts)))
    # A JSON string uses Flyte's native string transport and avoids pickle-based
    # transport for heterogeneous dictionaries.
    return json.dumps(results)


if __name__ == "__main__":
    required = ("MODEL_API_KEY", "MODEL_BASE_URL", "MODEL_NAME")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit("Missing environment variables: " + ", ".join(missing))

    flyte.init_from_config(".flyte/config.yaml")
    # Run-level environment variables are forwarded to the remote task pod.
    # This keeps provider configuration out of the task image and source code.
    provider_env = {
        name: os.environ[name]
        for name in (*required, "MODEL_PROVIDER")
        if name in os.environ
    }
    run = flyte.with_runcontext(env_vars=provider_env).run(
        run_experiment,
        prompts=PROMPTS,
    )
    print(f"Flyte run: {run.name}")
    print(f"Flyte URL: {run.url}")
    run.wait()

    output = {
        "run_name": run.name,
        "provider": os.environ.get("MODEL_PROVIDER", "custom"),
        "model": os.environ["MODEL_NAME"],
        "results": json.loads(run.result),
    }
    output_path = Path("work/results/open_model_experiment.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Saved results to {output_path}")
