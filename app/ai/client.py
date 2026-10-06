import requests

from app.config import OPENROUTER_API_KEY


URL = "https://openrouter.ai/api/v1/chat/completions"


def ask_ai(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "openrouter/free",
        "messages": messages,
    }

    response = requests.post(
        URL,
        headers=headers,
        json=data,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    return result["choices"][0]["message"]["content"]
