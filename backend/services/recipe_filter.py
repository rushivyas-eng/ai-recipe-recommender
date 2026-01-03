from typing import List, Dict, Any
from collections import Counter


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

NON_VEG_KEYWORDS = {
    "egg", "eggs",
    "fish", "fishes",
    "chicken", "hen",
    "mutton", "lamb",
    "beef", "pork",
    "meat",
    "prawn", "shrimp", "crab", "seafood"
}


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return (
        text.lower()
        .replace(",", " ")
        .replace("-", " ")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )


def extract_ingredients(ingredients) -> List[str]:
    """
    Extract ingredient names from complex ingredient schema.

    Supports:
    - list[str]
    - list[dict{name: str}]
    - dict[str, list[dict{name: str}]]
    """

    flat = []

    if isinstance(ingredients, list):
        for item in ingredients:
            if isinstance(item, str):
                flat.append(item)
            elif isinstance(item, dict) and "name" in item:
                flat.append(item["name"])

    elif isinstance(ingredients, dict):
        for group in ingredients.values():
            if isinstance(group, list):
                for item in group:
                    if isinstance(item, str):
                        flat.append(item)
                    elif isinstance(item, dict) and "name" in item:
                        flat.append(item["name"])

    return flat


# --------------------------------------------------
# CORE FILTER + RANK
# --------------------------------------------------

def filter_and_rank_recipes(
    recipes: List[Dict[str, Any]],
    detected_vegetables: List[str],
    optional_vegetables: List[str],
    cuisine: str,
    diet: str,
    cooking_time: int,
    persons: int,
    meal: str,
    top_k: int = 10,
):
    """
    Production-grade recipe recommender.
    Fully ingredient-aware, diet-safe, and robust.
    """

    available_vegetables = {
        normalize(v)
        for v in (detected_vegetables + optional_vegetables)
        if isinstance(v, str)
    }

    scored_recipes = []

    for recipe in recipes:
        score = 0.0

        # -----------------------------
        # INGREDIENT EXTRACTION
        # -----------------------------
        raw_ingredients = extract_ingredients(recipe.get("ingredients", []))
        recipe_ingredients = {normalize(i) for i in raw_ingredients}

        recipe_name_norm = normalize(recipe.get("name", ""))

        # -----------------------------
        # ABSOLUTE VEG FILTER (NO LEAKS)
        # -----------------------------
        if diet == "veg":
            # Block via ingredients
            if any(
                nv in ing
                for ing in recipe_ingredients
                for nv in NON_VEG_KEYWORDS
            ):
                continue

            # Block via recipe name (CRITICAL)
            if any(nv in recipe_name_norm for nv in NON_VEG_KEYWORDS):
                continue

        # -----------------------------
        # VEGETABLE MATCHING (SUBSTRING)
        # -----------------------------
        matched = set()

        for veg in available_vegetables:
            for ing in recipe_ingredients:
                if veg in ing:
                    matched.add(veg)

        # --------------------------------
        # REQUIRED INGREDIENTS
        # --------------------------------
        required_ingredients = set()

        ingredients_block = recipe.get("ingredients", {})

        # Base + Primary are required to cook
        for group in ["primary", "base"]:
            for item in ingredients_block.get(group, []):
                name = item.get("name")
                if name:
                    required_ingredients.add(normalize(name))

        # Ingredients user already has
        available = set(available_vegetables)

        # Missing = required - available
        missing_ingredients = sorted(required_ingredients - available)

        # --------------------------------
        # INGREDIENT COVERAGE
        # --------------------------------
        total_required = len(required_ingredients)

        if total_required > 0:
            coverage_ratio = len(matched) / total_required
        else:
            coverage_ratio = 0.0

        coverage_percent = round(coverage_ratio * 100)

        # Require at least one veg match
        if not matched:
            continue

        # -----------------------------
        # SCORING
        # -----------------------------
        score += len(matched) * 3.0

        # --------------------------------
        # STRICT CUISINE FILTER
        # --------------------------------
        if cuisine:
            recipe_cuisine = recipe.get("cuisine")
            if not recipe_cuisine:
                continue

            if recipe_cuisine.strip().lower() != cuisine.strip().lower():
                continue

        # Meal match (loose)
        if meal and recipe.get("meal"):
            if meal.lower() in recipe["meal"].lower():
                score += 0.5

        # Cooking time
        rt = recipe.get("cooking_time")
        if isinstance(rt, int):
            if rt <= cooking_time:
                score += 1.0
            elif rt <= cooking_time + 15:
                score += 0.5

        # -----------------------------
        # COLLECT RESULT
        # -----------------------------
        scored_recipes.append({
            "id": recipe.get("id"),
            "name": recipe.get("name"),
            "score": round(score, 2),
            "matched_vegetables": list(matched),
            "missing_ingredients": missing_ingredients,
            "required_ingredients": sorted(list(required_ingredients)),
            "coverage_percent": coverage_percent,
            "cuisine": recipe.get("cuisine"),
            "meal": recipe.get("meal"),
            "cooking_time": recipe.get("cooking_time"),
            "meta": recipe.get("meta", {})
        })


    # -----------------------------
    # SORT & RETURN
    # -----------------------------
    ranked = sorted(
        scored_recipes,
        key=lambda x: x["score"],
        reverse=True
    )

    # --------------------------------
    # SUGGEST INGREDIENT ADDITIONS
    # --------------------------------
    missing_counter = Counter()

    for recipe in ranked[:top_k]:
        for ing in recipe.get("missing_ingredients", []):
            missing_counter[ing] += 1

    suggested_additions = [
        ing for ing, _ in missing_counter.most_common(3)
    ]

    return {
        "recipes": ranked[:top_k],
        "suggested_additions": suggested_additions
    }

