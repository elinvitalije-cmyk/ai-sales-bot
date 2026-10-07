import json
from pathlib import Path


DATA_FILE = Path("data/products.json")


def load_catalog():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_tariff(family_id, speed):
    catalog = load_catalog()

    family = catalog["families"].get(family_id)

    if family is None:
        return None

    variant = family["variants"].get(str(speed))

    if variant is None:
        return None

    return {
        "family_id": family_id,
        "family_name": family["name"],
        "speed_mbps": variant["speed_mbps"],
        "promo_price": variant.get("promo_price"),
        "regular_price": variant.get("regular_price"),
        "tv_channels": family.get("tv_channels"),
        "movix": family.get("movix"),
        "segment": family.get("segment"),
    }


def get_catalog_for_ai():
    catalog = load_catalog()

    result = []

    for family_id, family in catalog["families"].items():
        for speed, variant in family["variants"].items():
            tariff = {
                "family_id": family_id,
                "name": family["name"],
                "speed_mbps": variant["speed_mbps"],
                "promo_price": variant.get("promo_price"),
                "promo_months": variant.get("promo_months"),
                "promo_requires_router_purchase": catalog["promo_requires_router_purchase"],
                "connection_fee": catalog["connection_fee"],
                "routers": catalog["routers"],
                "regular_price": variant.get("regular_price"),
                "tv_channels": family.get("tv_channels"),
                "movix": family.get("movix"),
                "segment": family.get("segment"),
            }

            result.append(tariff)

    return result
