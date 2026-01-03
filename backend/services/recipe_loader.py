import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.json"

def load_recipes():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)
