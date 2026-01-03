from typing import List


# -----------------------------
# CANONICAL VEGETABLE NAMES
# -----------------------------
VEG_SYNONYMS = {
    "tomatoes": "tomato",
    "tomato": "tomato",

    "onions": "onion",
    "onion": "onion",

    "potatoes": "potato",
    "potato": "potato",

    "capsicum": "bell_pepper",
    "bell pepper": "bell_pepper",
    "bell_pepper": "bell_pepper",

    "brinjal": "eggplant",
    "eggplant": "eggplant",

    "carrots": "carrot",
    "carrot": "carrot",

    "beans": "beans",
    "green beans": "beans",

    "green chilli": "green_chilli",
    "green chilli pepper": "green_chilli",
    "green_chilli": "green_chilli",

    "cabbage": "cabbage",
    "cauliflower": "cauliflower",

    "peas": "green_peas",
    "green peas": "green_peas"
}


def normalize_vegetable(name: str) -> str:
    """
    Normalize a single vegetable name into canonical form.
    """
    if not name:
        return ""

    cleaned = name.strip().lower()
    return VEG_SYNONYMS.get(cleaned, cleaned)


def normalize_vegetable_list(items: List[str]) -> List[str]:
    """
    Normalize a list of vegetable names.
    Removes duplicates and empty entries.
    """
    normalized = {normalize_vegetable(item) for item in items}
    return [item for item in normalized if item]
