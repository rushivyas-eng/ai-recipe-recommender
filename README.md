# 🍲 AI Recipe Recommender

An experimental AI-powered application that recommends cooking recipes based on
vegetables detected from an image, user preferences, and cuisine selection.

The goal of this project is to explore how computer vision, data processing, and
backend APIs can be combined to build a practical, user-centric recommendation system
using only open-source tools and datasets.

---

## 🚀 Key Features

- 📸 **Vegetable detection from image**
  - Uses a custom-trained image classifier
  - Detects vegetables from uploaded images

- 🧾 **Optional manual vegetable input**
  - Users can add vegetables they already have

- 🌍 **Dynamic cuisine selection**
  - Cuisine dropdown is populated directly from the dataset
  - Strict cuisine filtering (no cross-cuisine leakage)

- 🥕 **Ingredient awareness**
  - Clearly shows ingredients the user already has
  - Highlights missing ingredients required to cook each recipe

- 📊 **Ingredient coverage score**
  - Indicates how complete a recipe is with current ingredients

- 💡 **Smart ingredient suggestions**
  - Suggests additional ingredients to unlock more recipes

- ⏱️ **Preference-based filtering**
  - Cooking time
  - Meal type (Breakfast / Lunch / Dinner)
  - Vegetarian / Non-vegetarian option

---

## 🏗️ System Architecture




---

## 🛠️ Tech Stack

- **Python**
- **FastAPI** – backend REST API
- **Streamlit** – frontend UI
- **PyTorch** – vegetable image classifier
- **Pandas** – dataset processing
- **PIL / OpenCV** – image handling

All components are built using **open-source libraries**.

---

## 📂 Project Structure

ai-recipe-recommender/
├── backend/
│ ├── api/ # FastAPI routes
│ ├── services/ # Filtering & ranking logic
│ ├── ml/ # Vegetable classifier
│ ├── data/ # Processed recipe JSON
│ └── scripts/ # Dataset conversion scripts
│
├── frontend/
│ └── streamlit_app.py # Streamlit UI
│
├── data_raw/ # Raw datasets (CSV / images)
├── README.md
└── .gitignore


---

## ▶️ Running the Project Locally

### 1️⃣ Clone the repository

```bash
git clone https://github.com/RVs-Operation-Learn/ai-recipe-recommender.git
cd ai-recipe-recommender


2️⃣ Create & activate virtual environment
python -m venv .venv

Windows:
.venv\Scripts\activate

Linux / macOS
source .venv/bin/activate


3️⃣ Install dependencies
pip install -r requirements.txt


4️⃣ Start the backend (FastAPI)
python run.py

Backend runs at: 
http://127.0.0.1:8000


5️⃣ Start the frontend (Streamlit)
streamlit run frontend/streamlit_app.py

Frontend runs at:
http://localhost:8501


📝 Notes & Limitations
This project is experimental and built for learning purposes
Recipe images may not load for all recipes due to external website restrictions
Dataset quality directly affects recipe accuracy
The ranking logic is heuristic-based (not ML-ranked)

🤝 Contributions
This is a learning-focused project.
Feedback, suggestions, and improvements are welcome via issues or pull requests.

📄 License
This project uses publicly available datasets and open-source libraries.
Refer to individual datasets for their respective licenses.