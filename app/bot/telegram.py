import asyncio
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.ai.client import ask_ai
from app.ai.prompts import SYSTEM_PROMPT
from app.config import TELEGRAM_BOT_TOKEN
from app.sales.catalog import get_catalog_for_ai


def create_initial_history():
    catalog = get_catalog_for_ai()

    catalog_text = json.dumps(
        catalog,
        ensure_ascii=False,
        indent=2,
    )

    return [
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["messages"] = create_initial_history()

    await update.message.reply_text(
        "Привет! Я помогу подобрать подходящий тариф Дом.ру "
        "в Волгограде.\n\n"
        "Расскажите, как вы пользуетесь интернетом."
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_message = update.message.text

    if "messages" not in context.user_data:
        context.user_data["messages"] = create_initial_history()

    messages = context.user_data["messages"]

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    answer = await asyncio.to_thread(
        ask_ai,
        messages,
    )

    messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    await update.message.reply_text(answer)


def run_bot():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print("Telegram bot запущен.")

    application.run_polling()


if __name__ == "__main__":
    run_bot()
