import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Recipe Recommender",
    page_icon="🍲",
    layout="wide"
)

# -------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------
if "recommendation_result" not in st.session_state:
    st.session_state.recommendation_result = None

if "selected_recipe_ids" not in st.session_state:
    st.session_state.selected_recipe_ids = set()

if "recipe_missing_map" not in st.session_state:
    st.session_state.recipe_missing_map = {}

# -------------------------------
# API CALL
# -------------------------------
def call_recommend_api(
    image_file,
    cuisine,
    diet,
    cooking_time,
    persons,
    meal,
    optional_vegetables=""
):
    files = {
        "file": (image_file.name, image_file, image_file.type)
    }

    data = {
        "optional_vegetables": optional_vegetables,
        "cuisine": cuisine,
        "diet": diet,
        "cooking_time": cooking_time,
        "persons": persons,
        "meal": meal
    }

    resp = requests.post(
        f"{API_URL}/recommend-from-image",
        files=files,
        data=data
    )
    resp.raise_for_status()
    return resp.json()

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.title("🧾 Preferences")

uploaded_file = st.sidebar.file_uploader(
    "Upload vegetable image",
    type=["jpg", "jpeg", "png"]
)

cuisine = st.sidebar.selectbox(
    "Cuisine style",
    ["north_indian", "south_indian", "gujarati", "andhra", "italian", "mexican", "asian"]
)

diet = st.sidebar.radio("Diet", ["veg", "non-veg"])
meal = st.sidebar.selectbox("Meal", ["breakfast", "lunch", "dinner"])
cooking_time = st.sidebar.selectbox("Cooking time (minutes)", [15, 30, 45, 60])
persons = st.sidebar.selectbox("Servings", [1, 2, 3, 4])

optional_vegetables = st.sidebar.text_input(
    "Optional vegetables (comma-separated)",
    placeholder="onion, tomato"
)

# -------------------------------
# MAIN ACTION
# -------------------------------
st.title("🍲 AI Recipe Recommender")
st.caption("Upload a vegetable image and get personalized recipe suggestions")
st.divider()

if st.button("🔍 Recommend Recipes", use_container_width=True):
    if not uploaded_file:
        st.error("Please upload an image first.")
    else:
        with st.spinner("Detecting vegetables and finding recipes..."):
            result = call_recommend_api(
                image_file=uploaded_file,
                cuisine=cuisine,
                diet=diet,
                cooking_time=cooking_time,
                persons=persons,
                meal=meal,
                optional_vegetables=optional_vegetables
            )

            st.session_state.recommendation_result = result
            st.session_state.selected_recipe_ids = set()
            st.session_state.recipe_missing_map = {}

# -------------------------------
# RENDER RESULTS
# -------------------------------
result = st.session_state.recommendation_result

if result:
    detected = result.get("detected_vegetables", [])
    recipes = result.get("recipes", [])

    st.success(f"🥕 Detected vegetables: {', '.join(detected) if detected else 'None'}")
    st.header(f"🍽️ Recommended Recipes ({len(recipes)})")

    for recipe in recipes:
        recipe_id = recipe["id"]
        recipe_name = recipe["name"]

        missing = recipe.get("missing_ingredients", [])
        matched = recipe.get("matched_vegetables", [])

        # Persist missing ingredients per recipe (NO LOGIC CHANGE)
        st.session_state.recipe_missing_map[recipe_id] = set(missing)

        total_time = (
            recipe.get("cooking_time")
            or recipe.get("meta", {}).get("total_time")
            or recipe.get("meta", {}).get("TotalTimeInMins")
            or "N/A"
        )

        # -------------------------------
        # RECIPE CARD (UI POLISH)
        # -------------------------------
        with st.container(border=True):

            # Header row: title + checkbox
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"## {recipe_name}")
            with col2:
                checked = recipe_id in st.session_state.selected_recipe_ids
                if st.checkbox(
                    "Add",
                    value=checked,
                    key=f"select_{recipe_id}"
                ):
                    st.session_state.selected_recipe_ids.add(recipe_id)
                else:
                    st.session_state.selected_recipe_ids.discard(recipe_id)

            st.caption(f"⏱️ Total Time: {total_time} mins | 🍽️ Cuisine: {recipe.get('cuisine')}")

            if matched:
                st.success(f"✅ You have: {', '.join(matched)}")

            if missing:
                st.warning(f"⚠️ You’ll also need: {', '.join(missing)}")

            st.markdown("**📊 Ingredient coverage**")
            st.progress(recipe.get("coverage_percent", 0) / 100)
            st.caption(f"{recipe.get('coverage_percent', 0)}% ingredients available")

            st.info(
                "💡 **Why this recipe?**\n\n"
                f"- You already have: {', '.join(matched) if matched else 'some ingredients'}\n"
                f"- Only {len(missing)} more ingredients needed\n"
                f"- Matches your selected cuisine\n"
                f"- Fits within your cooking time"
            )

            with st.expander("📖 View Instructions"):
                st.write(recipe.get("meta", {}).get("instructions", "No instructions available."))

            if recipe.get("meta", {}).get("recipe_url"):
                st.link_button("🔗 Open Full Recipe", recipe["meta"]["recipe_url"])

    # -------------------------------
    # SHOPPING LIST (UI POLISH ONLY)
    # -------------------------------
    if st.session_state.selected_recipe_ids:
        shopping_items = set()

        for rid in st.session_state.selected_recipe_ids:
            shopping_items |= st.session_state.recipe_missing_map.get(rid, set())

        st.divider()
        st.header("🛒 Shopping List")
        st.caption(
            "Based on the recipes you selected above. "
            "Uncheck items as you buy them."
        )

        for item in sorted(shopping_items):
            st.checkbox(item, key=f"shop_{item}")
    else:
        st.divider()
        st.info("Select one or more recipes above to generate a shopping list.")
