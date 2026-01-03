import streamlit as st
import requests
from io import BytesIO
from PIL import Image

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
    """Safely load external recipe images (handles hotlink blocking)."""
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
    # IMPORTANT: use getvalue() to avoid stream exhaustion
    image_bytes = image_file.getvalue()

    if not image_bytes:
        raise ValueError("Uploaded image is empty")

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
        st.error("❌ Backend error")
        st.code(resp.text)
        resp.raise_for_status()

    return resp.json()


@st.cache_data
def fetch_cuisines():
    resp = requests.get("http://127.0.0.1:8000/metadata/cuisines")
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

    cuisine_options.insert(0, {
        "label": "Any cuisine",
        "value": "any"
    })

    selected_cuisine = st.selectbox(
        "Cuisine style",
        cuisine_options,
        format_func=lambda x: x["label"]
    )

    cuisine_value = selected_cuisine["value"]

    diet = st.radio("Diet", ["veg", "non-veg"], horizontal=True)

    meal = st.selectbox("Meal", ["breakfast", "lunch", "dinner"])

    cooking_time = st.selectbox(
        "Cooking time (minutes)",
        [15, 30, 45, 60]
    )

    persons = st.selectbox("Servings", [1, 2, 3, 4, 5, 6])

    optional_vegetables = st.text_input(
        "Optional vegetables (comma-separated)",
        placeholder="onion, tomato"
    )

# -----------------------------
# ACTION
# -----------------------------
if st.button("🔍 Recommend Recipes", use_container_width=True):

    if not uploaded_file:
        st.error("Please upload an image first.")
    else:
        with st.spinner("Detecting vegetables and finding recipes..."):
            result = call_recommend_api(
                image_file=uploaded_file,
                cuisine_value=cuisine_value,
                diet=diet,
                cooking_time=cooking_time,
                persons=persons,
                meal=meal,
                optional_vegetables=optional_vegetables
            )

        st.success(
            f"🥕 Detected vegetables: {', '.join(result['detected_vegetables']) or 'None'}"
        )

        suggestions = result.get("suggested_additions", [])

        if suggestions:
            st.info(
                f"💡 Add {', '.join(suggestions)} to unlock more recipes"
            )

        recipes = result.get("recipes", [])

        if not recipes:
            st.warning("No matching recipes found. Try changing preferences.")
        else:
            st.subheader(f"🍽️ Recommended Recipes ({len(recipes)})")

            for recipe in recipes:
                st.divider()

                col1, col2 = st.columns([1, 2])

                # IMAGE
                with col1:
                    img = load_recipe_image(recipe.get("meta", {}).get("image_url"))
                    if img:
                        st.image(img, use_column_width=True)
                    else:
                        st.info("📷 Image not available")

                # CONTENT
                with col2:
                    st.markdown(f"## {recipe['name']}")
                    st.markdown(f"**Score:** {recipe['score']}")
                    # Ingredients user has
                    if recipe.get("matched_vegetables"):
                        st.markdown("✅ **You have:**")
                        st.write(", ".join(recipe["matched_vegetables"]))

                    # Ingredients user is missing
                    if recipe.get("missing_ingredients"):
                        st.markdown("⚠️ **You’ll also need:**")
                        st.write(", ".join(recipe["missing_ingredients"]))

                    
                    coverage = recipe.get("coverage_percent", 0)

                    if coverage >= 70:
                        st.success(f"🟢 Ingredient coverage: {coverage}%")
                    elif coverage >= 40:
                        st.warning(f"🟡 Ingredient coverage: {coverage}%")
                    else:
                        st.error(f"🔴 Ingredient coverage: {coverage}%")


                    if recipe.get("cooking_time"):
                        st.markdown(f"⏱️ **Total Time:** {recipe['cooking_time']} mins")

                    st.markdown(
                        f"🍽️ **Style:** {recipe.get('meta', {}).get('original_cuisine', 'Unknown')}"
                    )

                    with st.expander("📖 View Instructions"):
                        st.write(recipe["meta"]["instructions"])

                    if recipe["meta"].get("recipe_url"):
                        st.link_button(
                            "🔗 Open Full Recipe",
                            recipe["meta"]["recipe_url"]
                        )
