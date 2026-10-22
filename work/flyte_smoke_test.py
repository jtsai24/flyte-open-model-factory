"""Run one minimal task on the local Flyte devbox."""

import flyte


env = flyte.TaskEnvironment(
    name="flyte_smoke_test",
    image=flyte.Image.from_debian_base(python_version=(3, 12)),
)


@env.task
def hello_flyte(message: str) -> str:
    return f"Flyte received: {message}"


if __name__ == "__main__":
    flyte.init_from_config(".flyte/config.yaml")
    run = flyte.run(hello_flyte, message="Hello from the local devbox")

    print(f"Flyte run: {run.name}")
    print(f"Flyte URL: {run.url}")
    run.wait()
    print(f"Result: {run.outputs()[0]}")
