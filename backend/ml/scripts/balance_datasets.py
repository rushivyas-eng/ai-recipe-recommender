from pathlib import Path
import random
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRAIN_DIR = PROJECT_ROOT / "backend" / "ml" / "data" / "train"

TARGET_MIN = 1000
IMG_EXTS = {".jpg", ".jpeg", ".png"}

for cls_dir in TRAIN_DIR.iterdir():
    if not cls_dir.is_dir():
        continue

    images = [p for p in cls_dir.iterdir() if p.suffix.lower() in IMG_EXTS]
    count = len(images)

    if count >= TARGET_MIN:
        print(f"Class '{cls_dir.name}' OK ({count})")
        continue

    print(f"Balancing '{cls_dir.name}' ({count} → {TARGET_MIN})")

    while len(images) < TARGET_MIN:
        img = random.choice(images)
        new_name = img.stem + "_dup_" + str(len(images)) + img.suffix
        shutil.copy(img, cls_dir / new_name)
        images.append(cls_dir / new_name)

print("✅ Dataset balancing complete")
