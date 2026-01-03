import torch
from torchvision import models, transforms
from PIL import Image
from pathlib import Path

# =====================================================
# PATHS
# =====================================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "veg_classifier.pt"

# =====================================================
# LOAD MODEL
# =====================================================
checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
CLASS_NAMES = checkpoint["classes"]

model = models.mobilenet_v2()
model.classifier[1] = torch.nn.Linear(
    model.classifier[1].in_features,
    len(CLASS_NAMES)
)
model.load_state_dict(checkpoint["model_state"])
model.eval().to(DEVICE)

# =====================================================
# IMAGE PREPROCESS
# =====================================================
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# =====================================================
# DETECTION FUNCTION
# =====================================================
def detect_vegetables(image: Image.Image):
    img = preprocess(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(img)
        probs = torch.softmax(outputs, dim=1)
        conf, pred = torch.max(probs, dim=1)

    vegetable = CLASS_NAMES[pred.item()]
    confidence = conf.item()

    return [{
        "name": vegetable,
        "confidence": round(confidence, 3)
    }]
