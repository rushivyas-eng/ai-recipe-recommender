import streamlit as st
import requests
from datetime import date, timedelta

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

# --- MEAL PLANNER (ISOLATED) ---
if "meal_plan" not in st.session_state:
    # { date_str: { meal: recipe_name } }
    st.session_state.meal_plan = {}

@st.cache_data
def fetch_cuisines():
    resp = requests.get(f"{API_URL}/metadata/cuisines")
    resp.raise_for_status()
    return resp.json()["cuisines"]

cuisine_options = fetch_cuisines()

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
    options=cuisine_options,
    format_func=lambda x: x["label"]
)["value"]

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

    # ----------------------------------
    # SUGGEST VEGETABLES TO UNLOCK MORE
    # ----------------------------------
    missing_counter = {}
    for recipe in recipes[:5]:
        for ing in recipe.get("missing_ingredients", []):
            missing_counter[ing] = missing_counter.get(ing, 0) + 1

    suggested = sorted(missing_counter.items(), key=lambda x: x[1], reverse=True)[:3]
    if suggested:
        st.info(f"💡 Add {', '.join([x[0] for x in suggested])} to unlock more recipes")

    st.header(f"🍽️ Recommended Recipes ({len(recipes)})")

    for recipe in recipes:
        recipe_id = recipe["id"]
        recipe_name = recipe["name"]

        missing = recipe.get("missing_ingredients", [])
        matched = recipe.get("matched_vegetables", [])

        st.session_state.recipe_missing_map[recipe_id] = set(missing)

        total_time = (
            recipe.get("cooking_time")
            or recipe.get("meta", {}).get("total_time")
            or "N/A"
        )

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"## {recipe_name}")
            with col2:
                checked = recipe_id in st.session_state.selected_recipe_ids
                if st.checkbox("Add", value=checked, key=f"select_{recipe_id}"):
                    st.session_state.selected_recipe_ids.add(recipe_id)
                else:
                    st.session_state.selected_recipe_ids.discard(recipe_id)

            st.caption(f"⏱️ {total_time} mins | 🍽️ {recipe.get('cuisine')}")

            if matched:
                st.success(f"✅ You have: {', '.join(matched)}")
            if missing:
                st.warning(f"⚠️ You’ll also need: {', '.join(missing)}")

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
            # MEAL PLANNER (Option A + B)
            # -------------------------------
            st.markdown("### 🍱 Add to Meal Plan")

            plan_date = st.date_input(
                "Date",
                value=date.today(),
                key=f"date_{recipe_id}"
            )
            plan_meal = st.selectbox(
                "Meal",
                ["breakfast", "lunch", "dinner"],
                key=f"meal_{recipe_id}"
            )

            d = str(plan_date)
            existing_recipe = (
                st.session_state.meal_plan.get(d, {}).get(plan_meal)
            )

            if existing_recipe == recipe_name:
                st.info("📅 Already planned for this meal")

            button_label = (
                "🔁 Replace in Meal Plan" if existing_recipe else "➕ Add to Meal Plan"
            )

            if st.button(button_label, key=f"add_plan_{recipe_id}"):
                st.session_state.meal_plan.setdefault(d, {})
                st.session_state.meal_plan[d][plan_meal] = recipe_name
                st.rerun()

    # -------------------------------
    # SHOPPING LIST (SELECTED RECIPES)
    # -------------------------------
    if st.session_state.selected_recipe_ids:
        st.divider()
        st.header("🛒 Shopping List (Selected Recipes)")
        shopping_items = set()
        for rid in st.session_state.selected_recipe_ids:
            shopping_items |= st.session_state.recipe_missing_map.get(rid, set())
        for item in sorted(shopping_items):
            st.checkbox(item, key=f"shop_{item}")

    # -------------------------------
    # MEAL PLANNER PANEL
    # -------------------------------
    st.divider()
    st.header("📅 Meal Planner")

    if not st.session_state.meal_plan:
        st.info("No meals planned yet.")
    else:
        for d, meals in sorted(st.session_state.meal_plan.items()):
            st.subheader(d)
            for m, r in meals.items():
                st.markdown(f"**{m.title()}**: {r}")
                if st.button(f"❌ Remove {r}", key=f"rm_{d}_{m}_{r}"):
                    del st.session_state.meal_plan[d][m]
                    if not st.session_state.meal_plan[d]:
                        del st.session_state.meal_plan[d]
                    st.rerun()

    if st.button("🧹 Clear Meal Plan"):
        st.session_state.meal_plan = {}
        st.success("Meal plan cleared")
        st.rerun()

    # ======================================================
    # 🆕 WEEKLY MEAL OVERVIEW (READ-ONLY)
    # ======================================================
    st.divider()
    st.header("📆 Weekly Meal Overview")
    st.caption("Read-only view of your meal plan for the current week")

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday

    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        day_key = str(current_day)
        meals = st.session_state.meal_plan.get(day_key, {})

        with st.expander(current_day.strftime("%A, %d %b")):
            st.write(f"🥣 **Breakfast**: {meals.get('breakfast', '—')}")
            st.write(f"🍛 **Lunch**: {meals.get('lunch', '—')}")
            st.write(f"🌙 **Dinner**: {meals.get('dinner', '—')}")

    # ======================================================
    # 🗓️ SHOPPING LIST (MEAL PLAN)
    # ======================================================
    st.divider()
    st.header("🗓️ Shopping List (Meal Plan)")
    st.caption("Ingredients required for meals you planned above")

    meal_plan_items = set()

    for meals in st.session_state.meal_plan.values():
        for recipe_name in meals.values():
            for recipe in recipes:
                if recipe["name"] == recipe_name:
                    meal_plan_items |= set(
                        recipe.get("missing_ingredients", [])
                    )

    if meal_plan_items:
        for item in sorted(meal_plan_items):
            st.checkbox(item, key=f"meal_plan_shop_{item}")
    else:
        st.info("No ingredients needed yet. Plan some meals to generate this list.")
