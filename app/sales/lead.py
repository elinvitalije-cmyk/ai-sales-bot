import re


LEAD_STEPS = [
    "full_name",
    "phone",
    "address",
    "tariff",
    "call_time",
    "comment",
]


LEAD_QUESTIONS = {
    "full_name": "Укажите ФИО одной строкой: фамилия, имя, отчество.",
    "phone": "Укажите номер телефона для связи.",
    "address": (
        "Укажите полный адрес подключения: "
        "улица, номер дома и номер квартиры."
    ),
    "tariff": "Какой тариф вы выбрали или рассматриваете?",
    "call_time": "В какое время вам удобно принять звонок менеджера?",
    "comment": (
        "Есть ли дополнительный комментарий для менеджера? "
        "Если нет — напишите: нет."
    ),
}


def create_empty_lead():
    return {
        "full_name": None,
        "phone": None,
        "address": None,
        "tariff": None,
        "call_time": None,
        "comment": None,
    }


def is_valid_full_name(full_name):
    parts = full_name.split()
    return bool(parts) and all(part.isalpha() for part in parts)


def is_valid_phone(phone):
    phone = phone.strip()
    if re.fullmatch(r"(?:\+7|8)[0-9 ()-]*", phone) is None:
        return False

    digits = "".join(character for character in phone if character in "0123456789")
    return len(digits) == 11


def format_lead(lead):
    return (
        "Новая заявка\n\n"
        f"ФИО: {lead['full_name']}\n"
        f"Телефон: {lead['phone']}\n"
        f"Адрес: {lead['address']}\n"
        f"Тариф: {lead['tariff']}\n"
        f"Удобное время звонка: {lead['call_time']}\n"
        f"Комментарий: {lead['comment']}"
    )
