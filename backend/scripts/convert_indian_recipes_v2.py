import pandas as pd
import json
import re
from pathlib import Path
from tqdm import tqdm

# -----------------------------
# PATH SETUP
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_PATH = BASE_DIR / "data_raw" / "Cleaned_Indian_Food_Dataset.csv"
OUTPUT_PATH = BASE_DIR / "backend" / "data" / "recipes.json"

if not INPUT_PATH.exists():
    raise FileNotFoundError(f"Dataset not found at: {INPUT_PATH}")

# -----------------------------
# HELPERS
# -----------------------------
def norm(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    return text.strip()


PRIMARY_INGREDIENTS = {
    "potato", "brinjal", "eggplant", "okra", "paneer",
    "cauliflower", "cabbage", "beans", "carrot", "peas",
    "spinach", "mushroom", "capsicum", "bell pepper"
}

BASE_INGREDIENTS = {"onion", "tomato"}
AROMATICS = {"garlic", "ginger"}

SPICES = {
    "cumin", "mustard", "turmeric",
    "red chilli powder", "garam masala",
    "coriander powder"
}

def normalize_cuisine(cuisine: str) -> str:
    if not isinstance(cuisine, str):
        return ""
    return (
        cuisine.lower()
        .replace("&", "and")
        .replace("recipes", "")
        .strip()
        .replace(" ", "_")
    )


def split_ingredients(text):
    text = norm(text)
    parts = re.split(r",|and", text)
    return [p.strip() for p in parts if p.strip()]


def classify_ingredients(ingredient_list):
    result = {
        "primary": [],
        "base": [],
        "spices": [],
        "aromatics": [],
        "garnish": []
    }

    for raw in ingredient_list:
        item = raw.lower()

        for p in PRIMARY_INGREDIENTS:
            if p in item:
                result["primary"].append({"name": p, "required": True})

        for b in BASE_INGREDIENTS:
            if b in item:
                result["base"].append({"name": b, "required": True})

        for a in AROMATICS:
            if a in item:
                result["aromatics"].append({"name": a})

        for s in SPICES:
            if s in item:
                result["spices"].append({"name": s})

    # de-duplicate
    for k in result:
        seen = set()
        deduped = []
        for i in result[k]:
            if i["name"] not in seen:
                deduped.append(i)
                seen.add(i["name"])
        result[k] = deduped

    return result


# -----------------------------
# MAIN
# -----------------------------
def main():
    df = pd.read_csv(INPUT_PATH)

    recipes = []
    recipe_id = 1

    for _, row in tqdm(df.iterrows(), total=len(df)):
        name = row.get("TranslatedRecipeName")
        translated_ingredients = row.get("TranslatedIngredients")
        cleaned_ingredients = row.get("Cleaned-Ingredients")
        instructions = row.get("TranslatedInstructions")

        if not all(isinstance(x, str) for x in [name, translated_ingredients, cleaned_ingredients, instructions]):
            continue

        ingredient_list = split_ingredients(translated_ingredients)
        classified = classify_ingredients(ingredient_list)

        if not classified["primary"] and not classified["base"]:
            continue

        total_time = int(row.get("TotalTimeInMins", 30) or 30)

        original_cuisine = str(row.get("Cuisine", "")).strip()

        recipe = {
            "id": f"IN{recipe_id:05}",
            "name": name,
            "cuisine": normalize_cuisine(original_cuisine),
            "original_cuisine": original_cuisine,
            "meal": None,
            "cooking_time": total_time,

            "ingredients": classified,

            # 👇 THIS IS THE CRITICAL FIX
            "meta": {
                "translated_ingredients": translated_ingredients,
                "cleaned_ingredients": cleaned_ingredients,
                "instructions": instructions,
                "image_url": str(row.get("image-url", "")).strip(),
                "recipe_url": str(row.get("URL", "")).strip(),
                "original_cuisine": str(row.get("Cuisine", "")).strip(),
                "ingredient_count": int(row.get("Ingredient-count", 0) or 0)
            }
        }

        recipes.append(recipe)
        recipe_id += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(recipes)} recipes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
