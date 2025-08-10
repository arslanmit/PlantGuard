import functools
from typing import Dict

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18

CLASSES = ["powdery_mildew", "blight", "rust", "healthy"]
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@functools.lru_cache(maxsize=1)
def load_image_model(num_classes: int = len(CLASSES)) -> torch.nn.Module:
    model = resnet18(weights=ResNet18_Weights.DEFAULT)
    in_f = model.fc.in_features
    model.fc = torch.nn.Linear(in_f, num_classes)
    # TODO: load fine-tuned checkpoint from data/*.pt
    model.eval().to(_DEVICE)
    return model


def _tfm() -> T.Compose:
    w = ResNet18_Weights.DEFAULT
    return T.Compose(
        [
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=w.meta["mean"], std=w.meta["std"]),
        ]
    )


def predict_image(pil_img: Image.Image) -> Dict[str, float]:
    x = _tfm()(pil_img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        logits = load_image_model()(x)
        probs = F.softmax(logits, dim=1).cpu().squeeze().tolist()
    return {c: float(probs[i]) for i, c in enumerate(CLASSES)}
