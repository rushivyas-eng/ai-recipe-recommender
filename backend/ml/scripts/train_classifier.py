from pathlib import Path
import torch
from torchvision import datasets, models, transforms
from torch import nn, optim
from tqdm import tqdm

# =====================================================
# PATHS
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "backend" / "ml" / "data"
MODEL_PATH = PROJECT_ROOT / "backend" / "ml" / "veg_classifier.pt"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EPOCHS = 10
BATCH_SIZE = 32
LR = 1e-3

# =====================================================
# TRANSFORMS
# =====================================================
train_tfms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
])

val_tfms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# =====================================================
# DATASETS
# =====================================================
train_ds = datasets.ImageFolder(DATA_DIR / "train", transform=train_tfms)
val_ds = datasets.ImageFolder(DATA_DIR / "val", transform=val_tfms)

train_loader = torch.utils.data.DataLoader(
    train_ds, batch_size=BATCH_SIZE, shuffle=True
)
val_loader = torch.utils.data.DataLoader(
    val_ds, batch_size=BATCH_SIZE
)

NUM_CLASSES = len(train_ds.classes)
print("Classes:", train_ds.classes)

# =====================================================
# MODEL (TRANSFER LEARNING)
# =====================================================
model = models.mobilenet_v2(weights="IMAGENET1K_V1")

# Freeze feature extractor
for param in model.features.parameters():
    param.requires_grad = False

# Replace classifier
model.classifier[1] = nn.Linear(
    model.classifier[1].in_features,
    NUM_CLASSES
)

model = model.to(DEVICE)

# =====================================================
# TRAINING SETUP
# =====================================================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier.parameters(), lr=LR)

# =====================================================
# TRAINING LOOP
# =====================================================
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0

    for x, y in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        x, y = x.to(DEVICE), y.to(DEVICE)

        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    avg_loss = running_loss / len(train_loader)
    print(f"Epoch {epoch+1} - Train Loss: {avg_loss:.4f}")

# =====================================================
# SAVE MODEL
# =====================================================
torch.save(
    {
        "model_state": model.state_dict(),
        "classes": train_ds.classes
    },
    MODEL_PATH
)

print(f"✅ Model trained and saved to {MODEL_PATH}")