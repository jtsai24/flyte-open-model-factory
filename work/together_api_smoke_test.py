import os
import time

from together import Together


client = Together(api_key=os.environ["MODEL_API_KEY"])
started = time.perf_counter()

try:
    response = client.chat.completions.create(
        #model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "Explain what a durable workflow runtime does in three concise sentences.",
            }
        ],
    )
except Exception as error:
    print(f"Error: {type(error).__name__}: {error}")
    raise

print(response.choices[0].message.content)
print(f"Model: {response.model}")
print(f"Latency: {time.perf_counter() - started:.2f} seconds")
print(f"Usage: {response.usage}")
print(f"Finish reason: {response.choices[0].finish_reason}")
