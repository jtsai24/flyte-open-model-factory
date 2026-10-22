"""Compare two Together-hosted models with one prompt using Flyte child tasks."""

from __future__ import annotations

import asyncio
import json
import os
import time

import flyte


image = flyte.Image.from_debian_base(python_version=(3, 12)).with_pip_packages(
    "together==3.0.0",
)

model_env = flyte.TaskEnvironment(
    name="together_model_call",
    image=image,
    secrets=flyte.Secret(
        "together-api-key",
        as_env_var="MODEL_API_KEY",
    ),
)

comparison_env = flyte.TaskEnvironment(
    name="two_model_comparison",
    image=image,
    depends_on=[model_env],
)


@model_env.task
def call_model(prompt: str, model: str) -> str:
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
        result = {
            "model": response.model,
            "prompt": prompt,
            "response": response.choices[0].message.content or "",
            "latency_seconds": round(time.perf_counter() - started, 3),
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "error": None,
        }
    except Exception as error:
        result = {
            "model": model,
            "prompt": prompt,
            "response": None,
            "latency_seconds": round(time.perf_counter() - started, 3),
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "error": f"{type(error).__name__}: {error}",
        }
    return json.dumps(result)


@comparison_env.task
async def compare_models(prompt: str, models: list[str]) -> str:
    child_results = await asyncio.gather(
        *(call_model.aio(prompt=prompt, model=model) for model in models)
    )
    return json.dumps([json.loads(result) for result in child_results])


if __name__ == "__main__":
    flyte.init_from_config(".flyte/config.yaml")
    run = flyte.run(
        compare_models,
        prompt="Explain what a durable workflow runtime does in three concise sentences.",
        models=[
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "openai/gpt-oss-120b",
        ],
    )

    print(f"Flyte run: {run.name}")
    print(f"Flyte URL: {run.url}")
    run.wait()
    print(json.dumps(json.loads(run.outputs()[0]), indent=2))
