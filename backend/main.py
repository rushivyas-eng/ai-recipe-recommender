from backend.services.recipe_loader import load_recipes
from backend.services.recipe_filter import filter_and_rank_recipes


def main():
    recipes = load_recipes()

    # -----------------------
    # SIMULATED USER INPUT
    # -----------------------
    detected_vegetables = ["tomato", "onion"]
    optional_vegetables = ["carrot"]

    cuisine = "south_indian"
    diet = "veg"
    cooking_time = 40
    persons = 2
    meal = "breakfast"

    results = filter_and_rank_recipes(
        recipes=recipes,
        detected_vegetables=detected_vegetables,
        optional_vegetables=optional_vegetables,
        cuisine=cuisine,
        diet=diet,
        cooking_time=cooking_time,
        persons=persons,
        meal=meal
    )

    print("\nRecommended Recipes:\n")

    for r in results:
        print(
            f"{r['name']} | "
            f"Score: {r['score']} | "
            f"Matched Veg: {r['matched_vegetables']} | "
            f"Time: {r['cooking_time']} mins"
        )


if __name__ == "__main__":
    main()
