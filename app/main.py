import json

from app.ai.client import ask_ai
from app.ai.prompts import SYSTEM_PROMPT
from app.sales.catalog import get_catalog_for_ai


def main():
    catalog = get_catalog_for_ai()

    catalog_text = json.dumps(
        catalog,
        ensure_ascii=False,
        indent=2,
    )

    messages = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\n\n"
                + "Доступный каталог тарифов:\n"
                + catalog_text
            ),
        }
    ]

    print("AI Sales Bot запущен.")
    print("Для выхода напиши: exit")
    print()

    while True:
        user_message = input("Ты: ")

        if user_message.lower() == "exit":
            print("Бот остановлен.")
            break

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        answer = ask_ai(messages)

        print(f"AI: {answer}")
        print()

        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


if __name__ == "__main__":
    main()

