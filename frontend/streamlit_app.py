import streamlit as st
import requests
from io import BytesIO
from PIL import Image

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "recipes" not in st.session_state:
    st.session_state.recipes = []

if "selected_recipes" not in st.session_state:
    st.session_state.selected_recipes = set()

if "detected_vegetables" not in st.session_state:
    st.session_state.detected_vegetables = []

if "suggested_additions" not in st.session_state:
    st.session_state.suggested_additions = []

# -----------------------------
# CONFIG
# -----------------------------
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Recipe Recommender",
    page_icon="🍲",
    layout="wide"
)

# -----------------------------
# HELPERS
# -----------------------------
def load_recipe_image(image_url: str):
    if not image_url:
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(image_url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return None
        return Image.open(BytesIO(resp.content))
    except Exception:
        return None


def call_recommend_api(
    image_file,
    cuisine_value,
    diet,
    cooking_time,
    persons,
    meal,
    optional_vegetables=""
):
    image_bytes = image_file.getvalue()

    files = {
        "file": (
            image_file.name,
            image_bytes,
            image_file.type or "image/jpeg"
        )
    }

    data = {
        "optional_vegetables": optional_vegetables,
        "cuisine": cuisine_value,
        "diet": diet,
        "cooking_time": str(cooking_time),
        "persons": str(persons),
        "meal": meal
    }

    resp = requests.post(
        f"{API_BASE_URL}/recommend-from-image",
        files=files,
        data=data
    )

    if resp.status_code != 200:
        st.error("Backend error")
        st.code(resp.text)
        resp.raise_for_status()

    return resp.json()


@st.cache_data
def fetch_cuisines():
    resp = requests.get(f"{API_BASE_URL}/metadata/cuisines")
    resp.raise_for_status()
    return resp.json()["cuisines"]

# -----------------------------
# UI HEADER
# -----------------------------
st.title("🍲 AI Recipe Recommender")
st.caption("Upload a vegetable image and get personalized recipe suggestions")
st.divider()

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
with st.sidebar:
    st.header("🧾 Preferences")

    uploaded_file = st.file_uploader(
        "Upload vegetable image",
        type=["jpg", "jpeg", "png"]
    )

    cuisine_options = fetch_cuisines()
    cuisine_options.insert(0, {"label": "Any cuisine", "value": "any"})

    selected_cuisine = st.selectbox(
        "Cuisine style",
        cuisine_options,
        format_func=lambda x: x["label"]
    )

    diet = st.radio("Diet", ["veg", "non-veg"], horizontal=True)
    meal = st.selectbox("Meal", ["breakfast", "lunch", "dinner"])
    cooking_time = st.selectbox("Cooking time (minutes)", [15, 30, 45, 60])
    persons = st.selectbox("Servings", [1, 2, 3, 4, 5, 6])

    optional_vegetables = st.text_input(
        "Optional vegetables (comma-separated)",
        placeholder="onion, tomato"
    )

# -----------------------------
# ACTION BUTTON
# -----------------------------
if st.button("🔍 Recommend Recipes", use_container_width=True):
    if not uploaded_file:
        st.error("Please upload an image first.")
    else:
        with st.spinner("Detecting vegetables and finding recipes..."):
            result = call_recommend_api(
                image_file=uploaded_file,
                cuisine_value=selected_cuisine["value"],
                diet=diet,
                cooking_time=cooking_time,
                persons=persons,
                meal=meal,
                optional_vegetables=optional_vegetables
            )

        st.session_state.recipes = result["recipes"]
        st.session_state.detected_vegetables = result.get("detected_vegetables", [])
        st.session_state.suggested_additions = result.get("suggested_additions", [])
        st.session_state.selected_recipes = set()

# -----------------------------
# RESULTS RENDERING (PERSISTENT)
# -----------------------------
if st.session_state.recipes:

    st.success(
        f"🥕 Detected vegetables: {', '.join(st.session_state.detected_vegetables) or 'None'}"
    )

    if st.session_state.suggested_additions:
        st.info(
            f"💡 Add {', '.join(st.session_state.suggested_additions)} to unlock more recipes"
        )

    st.subheader(f"🍽️ Recommended Recipes ({len(st.session_state.recipes)})")

    for recipe in st.session_state.recipes:
        recipe_id = recipe["id"]

        selected = st.checkbox(
            "Select recipe for shopping list",
            key=f"select_{recipe_id}"
        )

        if selected:
            st.session_state.selected_recipes.add(recipe_id)
        else:
            st.session_state.selected_recipes.discard(recipe_id)

        st.divider()
        col1, col2 = st.columns([1, 2])

        with col1:
            img = load_recipe_image(recipe.get("meta", {}).get("image_url"))
            if img:
                st.image(img, use_column_width=True)
            else:
                st.info("📷 Image not available")

        with col2:
            st.markdown(f"## {recipe['name']}")
            st.markdown(f"**Score:** {recipe['score']}")

            if recipe.get("matched_vegetables"):
                st.markdown("✅ **You have:**")
                st.write(", ".join(recipe["matched_vegetables"]))

            if recipe.get("missing_ingredients"):
                st.markdown("⚠️ **You’ll also need:**")
                st.write(", ".join(recipe["missing_ingredients"]))

            coverage = recipe.get("coverage_percent", 0)
            st.progress(coverage / 100)
            st.caption(f"Ingredient coverage: {coverage}%")

            if recipe.get("explanation"):
                st.markdown("💡 **Why this recipe?**")
                for reason in recipe["explanation"]:
                    st.write(f"• {reason}")

            if recipe.get("cooking_time"):
                st.markdown(f"⏱️ **Total Time:** {recipe['cooking_time']} mins")

            st.markdown(
                f"🍽️ **Style:** {recipe.get('meta', {}).get('original_cuisine', 'Unknown')}"
            )

            with st.expander("📖 View Instructions"):
                st.write(recipe["meta"]["instructions"])

            if recipe["meta"].get("recipe_url"):
                st.link_button("🔗 Open Full Recipe", recipe["meta"]["recipe_url"])

    # -----------------------------
    # SHOPPING LIST (SELECTED ONLY)
    # -----------------------------
    shopping_items = set()

    for recipe in st.session_state.recipes:
        if recipe["id"] in st.session_state.selected_recipes:
            for ing in recipe.get("missing_ingredients", []):
                shopping_items.add(ing)

    if shopping_items:
        st.markdown("## 🛒 Shopping List (Selected Recipes)")
        for item in sorted(shopping_items):
            st.checkbox(item, key=f"shop_{item}")
