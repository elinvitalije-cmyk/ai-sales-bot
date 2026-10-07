import asyncio
import json
import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.ai.client import ask_ai
from app.ai.prompts import SYSTEM_PROMPT
from app.config import (
    MANAGER_CHAT_ID,
    TELEGRAM_BOT_TOKEN,
)
from app.db.database import (
    get_leads_by_status,
    init_db,
    save_lead,
)
from app.sales.catalog import get_catalog_for_ai
from app.sales.lead import (
    LEAD_QUESTIONS,
    LEAD_STEPS,
    create_empty_lead,
    find_tariff,
    format_lead,
    is_valid_full_name,
    is_valid_phone,
)


START_LEAD_PATTERN = (
    r"\[START_LEAD:(.+?)\]"
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
    context.user_data["messages"] = (
        create_initial_history()
    )

    await update.message.reply_text(
        "Привет! Я помогу подобрать подходящий "
        "тариф Дом.ру в Волгограде.\n\n"
        "Расскажите, как вы пользуетесь интернетом."
    )


async def cancel_lead(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop(
        "lead_step",
        None,
    )

    context.user_data.pop(
        "lead",
        None,
    )

    context.user_data.pop(
        "pending_tariff",
        None,
    )

    await update.message.reply_text(
        "Оформление заявки отменено.\n\n"
        "Можете продолжить подбор тарифа."
    )


async def ask_tariff_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    tariff,
):
    context.user_data["pending_tariff"] = tariff

    keyboard = [
        [
            InlineKeyboardButton(
                "Да, подходит",
                callback_data="tariff_yes",
            ),
            InlineKeyboardButton(
                "Нет",
                callback_data="tariff_no",
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        f"Подтверждаете тариф «{tariff}»?",
        reply_markup=reply_markup,
    )


async def handle_tariff_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    await query.edit_message_reply_markup(
        reply_markup=None
    )

    if query.data == "tariff_no":
        context.user_data.pop(
            "pending_tariff",
            None,
        )

        await query.message.reply_text(
            "Хорошо. Продолжим подбор тарифа."
        )

        return

    tariff = context.user_data.pop(
        "pending_tariff",
        None,
    )

    if tariff is None:
        await query.message.reply_text(
            "Не удалось определить выбранный тариф. "
            "Давайте продолжим подбор."
        )
        return

    lead = create_empty_lead()

    lead["tariff"] = tariff

    context.user_data["lead"] = lead
    context.user_data["lead_step"] = 0

    first_field = LEAD_STEPS[0]

    await query.message.reply_text(
        f"Отлично. Вы выбрали «{tariff}».\n\n"
        "Давайте оформим заявку.\n\n"
        + LEAD_QUESTIONS[first_field]
        + "\n\n"
        + "Для отмены заявки отправьте /отмена"
    )


async def show_leads(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    current_chat_id = update.effective_chat.id

    if current_chat_id != int(
        MANAGER_CHAT_ID
    ):
        await update.message.reply_text(
            "Эта команда доступна только менеджеру."
        )
        return

    leads = get_leads_by_status("new")

    if not leads:
        await update.message.reply_text(
            "Новых заявок сейчас нет."
        )
        return

    latest_leads = leads[:5]

    messages = []

    for lead in latest_leads:
        lead_text = (
            f"Новая заявка #{lead['id']}\n"
            f"ФИО: {lead['full_name']}\n"
            f"Телефон: {lead['phone']}\n"
            f"Адрес: {lead['address']}\n"
            f"Тариф: {lead['tariff']}\n"
            f"Время звонка: {lead['call_time']}\n"
            f"Создана: {lead['created_at']}"
        )

        messages.append(
            lead_text
        )

    await update.message.reply_text(
        "\n\n────────────\n\n".join(
            messages
        )
    )


async def handle_lead_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    step = context.user_data["lead_step"]
    field = LEAD_STEPS[step]

    user_input = update.message.text.strip()

    if field == "full_name":
        if not is_valid_full_name(
            user_input
        ):
            await update.message.reply_text(
                "Укажите три части ФИО: "
                "фамилию, имя и отчество.\n\n"
                + LEAD_QUESTIONS["full_name"]
            )
            return

    if field == "phone":
        if not is_valid_phone(
            user_input
        ):
            await update.message.reply_text(
                "Номер должен начинаться с +7 или 8 "
                "и содержать 11 цифр.\n"
                "Например: +7 999 123-45-67.\n\n"
                + LEAD_QUESTIONS["phone"]
            )
            return

    context.user_data["lead"][field] = (
        user_input
    )

    step += 1

    if step >= len(LEAD_STEPS):
        lead = context.user_data["lead"]

        save_lead(lead)

        lead_text = format_lead(lead)

        await update.message.reply_text(
            "Спасибо! Заявка оформлена. "
            "Менеджер свяжется с вами."
        )

        await context.bot.send_message(
            chat_id=int(MANAGER_CHAT_ID),
            text=lead_text,
        )

        context.user_data.pop(
            "lead_step",
            None,
        )

        context.user_data.pop(
            "lead",
            None,
        )

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
    user_message = (
        update.message.text.strip()
    )

    if user_message.lower() == "/отмена":
        await cancel_lead(
            update,
            context,
        )
        return

    if "lead_step" in context.user_data:
        await handle_lead_message(
            update,
            context,
        )
        return

    if "messages" not in context.user_data:
        context.user_data["messages"] = (
            create_initial_history()
        )

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

    marker_match = re.search(
        START_LEAD_PATTERN,
        answer,
    )

    selected_tariff = None

    if marker_match:
        marker_tariff = (
            marker_match.group(1).strip()
        )

        selected_tariff = find_tariff(
            marker_tariff
        )

    clean_answer = re.sub(
        START_LEAD_PATTERN,
        "",
        answer,
    ).strip()

    messages.append(
        {
            "role": "assistant",
            "content": clean_answer,
        }
    )

    if clean_answer:
        await update.message.reply_text(
            clean_answer
        )

    if marker_match and selected_tariff is None:
        await update.message.reply_text(
            "Не удалось корректно зафиксировать "
            "выбранный тариф. "
            "Давайте уточним вариант ещё раз."
        )
        return

    if selected_tariff:
        await ask_tariff_confirmation(
            update,
            context,
            selected_tariff,
        )


def run_bot():
    init_db()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "leads",
            show_leads,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_tariff_confirmation,
            pattern=r"^tariff_(yes|no)$",
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT,
            handle_message,
        )
    )

    print("Telegram bot запущен.")

    application.run_polling()


if __name__ == "__main__":
    run_bot()
