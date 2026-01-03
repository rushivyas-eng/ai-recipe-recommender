import pandas as pd
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_PATH = BASE_DIR / "data_raw" / "Cleaned_Indian_Food_Dataset.csv"
OUTPUT_PATH = BASE_DIR / "backend" / "data" / "recipes_meta.json"

df = pd.read_csv(INPUT_PATH)

meta = {}
for idx, row in df.iterrows():
    recipe_id = f"IN{idx+1:05}"

    meta[recipe_id] = {
        "translated_ingredients": row.get("TranslatedIngredients", ""),
        "cleaned_ingredients": row.get("Cleaned-Ingredients", ""),
        "instructions": row.get("TranslatedInstructions", ""),
        "image_url": row.get("image-url", ""),
        "recipe_url": row.get("URL", ""),
        "original_cuisine": row.get("Cuisine", ""),
        "total_time": row.get("TotalTimeInMins"),
        "ingredient_count": row.get("Ingredient-count"),
    }

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

print(f"Saved metadata for {len(meta)} recipes → {OUTPUT_PATH}")
