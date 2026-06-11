import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

if GROQ_API_KEY is None:
    raise RuntimeError("GROQ_API_KEY is not set in environment or .env file.")

# Groq exposes an OpenAI-compatible API, so we use the OpenAI client with a custom base_url.[web:59][web:64]
client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Calls Groq's OpenAI-compatible chat completions API and returns the assistant message content as string.
    """
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content
