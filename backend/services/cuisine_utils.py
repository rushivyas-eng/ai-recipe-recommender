def normalize_cuisine(cuisine: str) -> str:
    return (
        cuisine.lower()
        .replace("&", "and")
        .replace("recipes", "")
        .strip()
        .replace(" ", "_")
    )
