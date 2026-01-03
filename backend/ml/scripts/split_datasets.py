from pathlib import Path
import random
import shutil

# =====================================================
# PATHS
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "backend" / "ml" / "data_unified"
OUT_DIR = PROJECT_ROOT / "backend" / "ml" / "data"

TRAIN_RATIO = 0.8
IMG_EXTS = {".jpg", ".jpeg", ".png"}

# =====================================================
# PREP OUTPUT DIRS
# =====================================================
for split in ["train", "val"]:
    (OUT_DIR / split).mkdir(parents=True, exist_ok=True)

# =====================================================
# SPLIT DATA
# =====================================================
for cls_dir in SRC_DIR.iterdir():
    if not cls_dir.is_dir():
        continue

    images = [p for p in cls_dir.iterdir() if p.suffix.lower() in IMG_EXTS]
    random.shuffle(images)

    split_idx = int(len(images) * TRAIN_RATIO)
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]

    for split, imgs in [("train", train_imgs), ("val", val_imgs)]:
        target_dir = OUT_DIR / split / cls_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)

        for img in imgs:
            shutil.copy(img, target_dir / img.name)

    print(
        f"Class '{cls_dir.name}': "
        f"{len(train_imgs)} train / {len(val_imgs)} val"
    )

print("✅ Train/Validation split complete")
