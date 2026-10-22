"""Run one Together AI call as a Flyte task."""

import os

import flyte


env = flyte.TaskEnvironment(
    name="flyte_together_smoke_test",
    image=flyte.Image.from_debian_base(python_version=(3, 12)).with_pip_packages(
        "together==3.0.0",
    ),
    secrets=flyte.Secret(
        "together-api-key",
        as_env_var="MODEL_API_KEY",
    ),
)


@env.task
def call_together(prompt: str, model: str) -> str:
    from together import Together

    client = Together(api_key=os.environ["MODEL_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


if __name__ == "__main__":
    flyte.init_from_config(".flyte/config.yaml")
    run = flyte.run(
        call_together,
        prompt="Explain what a durable workflow runtime does in three concise sentences.",
        model="openai/gpt-oss-120b",
    )

    print(f"Flyte run: {run.name}")
    print(f"Flyte URL: {run.url}")
    run.wait()
    print(f"Result: {run.outputs()[0]}")
