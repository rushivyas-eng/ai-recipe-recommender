from fastapi import UploadFile, File, Depends, Form
from PIL import Image
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from io import BytesIO
from backend.services.recipe_loader import load_recipes
from backend.services.recipe_filter import filter_and_rank_recipes
from backend.services.normalize import normalize_vegetable_list
from backend.ml.veg_detector import detect_vegetables

router = APIRouter()


# -----------------------------
# REQUEST MODEL
# -----------------------------
class RecipeRequest(BaseModel):
    detected_vegetables: List[str]
    optional_vegetables: List[str]
    cuisine: str
    diet: str
    cooking_time: int
    persons: int
    meal: str




# -----------------------------
# HEALTH CHECK
# -----------------------------
@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/detect-vegetables")
async def detect_vegetables_api(file: UploadFile = File(...)):
    image = Image.open(file.file).convert("RGB")

    detected = detect_vegetables(image)

    return {
        "detected_vegetables": detected
    }


@router.get("/metadata/cuisines")
def get_cuisines():
    recipes = load_recipes()

    cuisine_map = {}

    for r in recipes:
        norm = r.get("cuisine")
        label = r.get("original_cuisine")

        if norm and label:
            cuisine_map[norm] = label

    cuisines = [
        {"label": label, "value": value}
        for value, label in sorted(cuisine_map.items())
    ]

    return {"cuisines": cuisines}



@router.post("/recommend-from-image")
async def recommend_from_image(
    file: UploadFile = File(...),

    optional_vegetables: str = Form(""),
    cuisine: str = Form(...),
    diet: str = Form(...),
    cooking_time: int = Form(60),
    persons: int = Form(2),
    meal: str = Form(...)
):
    # 1️⃣ Load image
    image_bytes = await file.read()
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # 2️⃣ Detect vegetables
    raw_detections = detect_vegetables(image)
    detected = [
        d["name"] for d in raw_detections if d["confidence"] >= 0.6
    ]

    # 3️⃣ Parse & normalize optional vegetables
    optional_list = [
        v.strip() for v in optional_vegetables.split(",") if v.strip()
    ]
    normalized_optional = normalize_vegetable_list(optional_list)

    # 4️⃣ Load recipes
    recipes = load_recipes()

    if cooking_time <= 0:
        cooking_time = 60

    if persons <= 0:
        persons = 2

    # 5️⃣ Recommend
    results = filter_and_rank_recipes(
        recipes=recipes,
        detected_vegetables=detected,
        optional_vegetables=normalized_optional,
        cuisine=cuisine,
        diet=diet,
        cooking_time=cooking_time,
        persons=persons,
        meal=meal,
    )

    return {
        "detected_vegetables": detected,
        "count": len(results),
        "recipes": results["recipes"],
        "suggested_additions": results["suggested_additions"],
        "shopping_list": results["shopping_list"]
    }


# -----------------------------
# RECOMMENDATION ENDPOINT
# -----------------------------
@router.post("/recommend")
def recommend_recipes(request: RecipeRequest):
    recipes = load_recipes()

    normalized_detected = normalize_vegetable_list(
        request.detected_vegetables
    )

    normalized_optional = normalize_vegetable_list(
        request.optional_vegetables
    )

    results = filter_and_rank_recipes(
        recipes=recipes,
        detected_vegetables=normalized_detected,
        optional_vegetables=normalized_optional,
        cuisine=request.cuisine,
        diet=request.diet,
        cooking_time=request.cooking_time,
        persons=request.persons,
        meal=request.meal,
    )


    return {
        "count": len(results),
        "recipes": results
    }
