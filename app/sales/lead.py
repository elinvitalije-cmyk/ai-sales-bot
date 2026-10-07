import re

from app.sales.catalog import get_catalog_for_ai


LEAD_STEPS = [
    "full_name",
    "phone",
    "address",
    "call_time",
]


LEAD_QUESTIONS = {
    "full_name": (
        "Укажите ФИО одной строкой: "
        "фамилия, имя, отчество."
    ),
    "phone": "Укажите номер телефона для связи.",
    "address": (
        "Укажите полный адрес подключения: "
        "улица, номер дома и номер квартиры."
    ),
    "call_time": (
        "В какое время вам удобно принять звонок менеджера?"
    ),
}


def create_empty_lead():
    return {
        "full_name": None,
        "phone": None,
        "address": None,
        "tariff": None,
        "call_time": None,

        # Пока оставляем для совместимости
        # с существующей SQLite-базой.
        "comment": None,
    }


def is_valid_full_name(full_name):
    parts = full_name.split()

    if len(parts) != 3:
        return False

    for part in parts:
        if re.fullmatch(
            r"[A-Za-zА-Яа-яЁё-]+",
            part,
        ) is None:
            return False

    return True


def is_valid_phone(phone):
    phone = phone.strip()

    if re.fullmatch(
        r"(?:\+7|8)[0-9 ()-]*",
        phone,
    ) is None:
        return False

    digits = "".join(
        character
        for character in phone
        if character.isdigit()
    )

    return len(digits) == 11


def normalize_tariff_name(text):
    return " ".join(
        text.lower()
        .replace("ё", "е")
        .split()
    )


def get_available_tariffs():
    catalog = get_catalog_for_ai()

    tariffs = []

    for tariff in catalog:
        tariff_name = (
            f"{tariff['name']} "
            f"{tariff['speed_mbps']}"
        )

        tariffs.append(tariff_name)

    return tariffs


def find_tariff(user_input):
    normalized_input = normalize_tariff_name(
        user_input
    )

    for tariff_name in get_available_tariffs():
        normalized_tariff = normalize_tariff_name(
            tariff_name
        )

        if normalized_input == normalized_tariff:
            return tariff_name

    return None


def format_lead(lead):
    return (
        "Новая заявка\n\n"
        f"ФИО: {lead['full_name']}\n"
        f"Телефон: {lead['phone']}\n"
        f"Адрес: {lead['address']}\n"
        f"Тариф: {lead['tariff']}\n"
        f"Удобное время звонка: {lead['call_time']}"
    )
