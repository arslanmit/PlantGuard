"""Computer vision module for plant disease detection."""

import functools

import torch
from PIL import Image
from torch.nn import functional
from torchvision import transforms
from torchvision.models import ResNet18_Weights, resnet18

CLASSES = ["powdery_mildew", "blight", "rust", "healthy"]
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@functools.lru_cache(maxsize=1)
def load_image_model(num_classes: int = len(CLASSES)) -> torch.nn.Module:
    model: torch.nn.Module = resnet18(weights=ResNet18_Weights.DEFAULT)
    in_f = model.fc.in_features  # type: ignore[union-attr]
    model.fc = torch.nn.Linear(in_f, num_classes)  # type: ignore[arg-type]
    # TODO: load fine-tuned checkpoint from data/*.pt
    model.eval()
    model.to(_DEVICE)
    return model


def _tfm() -> transforms.Compose:
    # Standard ImageNet normalization values
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def predict_image(pil_img: Image.Image) -> dict[str, float]:
    x = _tfm()(pil_img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        logits = load_image_model()(x)
        probs = functional.softmax(logits, dim=1).cpu().squeeze().tolist()
    return {c: float(probs[i]) for i, c in enumerate(CLASSES)}
