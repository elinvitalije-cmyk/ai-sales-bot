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
from app.config import MANAGER_CHAT_ID, TELEGRAM_BOT_TOKEN
from app.sales.catalog import get_catalog_for_ai
from app.sales.lead import (
    LEAD_QUESTIONS,
    LEAD_STEPS,
    create_empty_lead,
    format_lead,
    is_valid_phone,
    is_valid_full_name,
)

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


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["messages"] = create_initial_history()

    await update.message.reply_text(
        "Привет! Я помогу подобрать подходящий тариф Дом.ру "
        "в Волгограде.\n\n"
        "Расскажите, как вы пользуетесь интернетом."
    )


async def my_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"Ваш chat_id: {chat_id}"
    )


async def start_lead(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["lead"] = create_empty_lead()
    context.user_data["lead_step"] = 0

    first_field = LEAD_STEPS[0]

    await update.message.reply_text(
        "Хорошо, давайте оформим данные для заявки.\n\n"
        + LEAD_QUESTIONS[first_field]
    )


async def handle_lead_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    step = context.user_data["lead_step"]

    field = LEAD_STEPS[step]

    if field == "full_name" and not is_valid_full_name(update.message.text):
        await update.message.reply_text(
            "ФИО должно содержать только буквы и пробелы, без цифр.\n"
            + LEAD_QUESTIONS["full_name"]
        )
        return

    if field == "phone" and not is_valid_phone(update.message.text):
        await update.message.reply_text(
            "Номер должен начинаться с +7 или 8 и содержать 11 цифр. Например: +7 999 123-45-67.\n"
            + LEAD_QUESTIONS["phone"]
        )
        return

    context.user_data["lead"][field] = update.message.text

    step += 1

    if step >= len(LEAD_STEPS):
        lead = context.user_data["lead"]

        lead_text = format_lead(lead)

        await update.message.reply_text(
            "Спасибо! Данные заявки собраны. "
            "Менеджер свяжется с вами."
        )

        await context.bot.send_message(
            chat_id=int(MANAGER_CHAT_ID),
            text=lead_text,
        )

        del context.user_data["lead_step"]
        del context.user_data["lead"]

        return

    context.user_data["lead_step"] = step

    next_field = LEAD_STEPS[step]

    await update.message.reply_text(
        LEAD_QUESTIONS[next_field]
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if "lead_step" in context.user_data:
        await handle_lead_message(update, context)
        return

    user_message = update.message.text

    print("CHAT_ID:", update.effective_chat.id)

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
        CommandHandler("myid", my_id)
    )

    application.add_handler(
        CommandHandler("lead", start_lead)
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
