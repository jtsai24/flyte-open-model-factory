import os

from together import Together


client = Together(api_key=os.environ["MODEL_API_KEY"])

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[
        {
            "role": "user",
            "content": "Explain what a durable workflow runtime does in three concise sentences.",
        }
    ],
)

print(response.choices[0].message.content)
