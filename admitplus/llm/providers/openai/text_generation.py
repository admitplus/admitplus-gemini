import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_openai(messages: list) -> str:
    model = os.getenv("OPENAI_TEXT_MODEL_DEFAULT")
    if not model:
        raise RuntimeError("Missing OPENAI_TEXT_MODEL_DEFAULT environment variable")

    response = client.chat.completions.create(
        model=model, messages=messages, temperature=0.7, max_tokens=2000
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from OpenAI")

    return content
