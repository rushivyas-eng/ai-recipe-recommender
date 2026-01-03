from pathlib import Path
import shutil

# =====================================================
# PATHS (MATCH YOUR PROJECT STRUCTURE)
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]   # ai-recipe-recommender/
DATA_RAW_DIR = PROJECT_ROOT / "data_raw"
ML_DIR = PROJECT_ROOT / "backend" / "ml"
OUT_DIR = ML_DIR / "data_unified"

# =====================================================
# DATASET FOLDERS (EXACT NAMES)
# =====================================================
DATASETS = [
    DATA_RAW_DIR / "dataset_veg_1",
    DATA_RAW_DIR / "dataset_veg_2",
]

# =====================================================
# CLASS MAPPING
# =====================================================
CLASS_MAP = {
    "tomato": ["tomato"],
    "onion": ["onion"],
    "potato": ["potato"],
    "cabbage": ["cabbage"],
    "cauliflower": ["cauliflower"],
    "carrot": ["carrot"],
    "capsicum": ["capsicum", "bell pepper"],
    "brinjal": ["brinjal", "eggplant"],
    "peas": ["peas", "green peas"],
}

# =====================================================
# PREP OUTPUT DIRS
# =====================================================
OUT_DIR.mkdir(exist_ok=True, parents=True)
for cls in CLASS_MAP:
    (OUT_DIR / cls).mkdir(exist_ok=True)

def norm(name: str) -> str:
    return name.lower().replace("_", " ").strip()

# =====================================================
# COPY IMAGES
# =====================================================
copied = 0

for dataset in DATASETS:
    if not dataset.exists():
        print(f"⚠️ Dataset not found: {dataset}")
        continue

    for split in ["train", "test", "validation"]:
        split_path = dataset / split
        if not split_path.exists():
            continue

        for folder in split_path.iterdir():
            if not folder.is_dir():
                continue

            folder_norm = norm(folder.name)

            for target, aliases in CLASS_MAP.items():
                if any(alias in folder_norm for alias in aliases):
                    for img in folder.iterdir():
                        if img.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                            continue

                        dst = OUT_DIR / target / f"{dataset.name}_{split}_{img.name}"
                        shutil.copy(img, dst)
                        copied += 1

print(f"✅ Dataset merge complete. Images copied: {copied}")
