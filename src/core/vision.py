import functools

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18

CLASSES = ["powdery_mildew", "blight", "rust", "healthy"]
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@functools.lru_cache(maxsize=1)
def load_image_model(num_classes: int = len(CLASSES)) -> torch.nn.Module:
    model: torch.nn.Module = resnet18(weights=ResNet18_Weights.DEFAULT)
    in_f = model.fc.in_features  # type: ignore
    model.fc = torch.nn.Linear(in_f, num_classes)  # type: ignore
    # TODO: load fine-tuned checkpoint from data/*.pt
    model.eval()
    model.to(_DEVICE)
    return model


def _tfm() -> T.Compose:
    # Standard ImageNet normalization values
    return T.Compose(
        [
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def predict_image(pil_img: Image.Image) -> dict[str, float]:
    x = _tfm()(pil_img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        logits = load_image_model()(x)
        probs = F.softmax(logits, dim=1).cpu().squeeze().tolist()
    return {c: float(probs[i]) for i, c in enumerate(CLASSES)}
