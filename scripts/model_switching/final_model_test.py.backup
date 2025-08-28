#!/usr/bin/env python3
"""Final comprehensive test of the integrated Hugging Face model."""

import json
import sys
from pathlib import Path

from PIL import Image

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.core.huggingface_vision import HuggingFaceVisionAdapter


def comprehensive_test() -> None:
    """Run comprehensive test on all 21 images."""
    print("🌱 PlantGuard Final Model Test")
    print("Using: Abhiram4/PlantDiseaseDetectorVit2 (Vision Transformer)")
    print("=" * 70)

    # Initialize adapter
    adapter = HuggingFaceVisionAdapter(device="cpu")

    if not adapter.is_loaded:
        print("❌ Failed to load model")
        return

    print(f"✅ Model loaded: {adapter.model_name}")
    print(f"📊 Classes: {len(adapter.class_names)}")
    print()

    # Load test metadata (guarded). Exit if metadata not present.
    metadata = {"sample_images": []}
    metadata_path = Path("data/raw/sample_images_metadata.json")
    if not metadata_path.exists():
        print("⚠️ sample_images_metadata.json not found; skipping final model test.")
        return
    try:
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception:
        print("⚠️ Failed to read sample_images_metadata.json; skipping final model test.")
        return

    # Test all images
    results = []
    perfect_matches = 0
    plant_matches = 0
    status_matches = 0

    print("🔍 Testing all 21 images:")
    print("-" * 70)

    for sample in metadata.get("sample_images", []):
        image_path = Path("data/raw") / sample.get("filename", "")

        if not image_path.exists():
            continue

        # Load image and predict
        image = Image.open(image_path)
        raw_class, readable_name, confidence, plant_type = adapter.predict_with_readable_name(image)

        # Ground truth
        gt_plant = sample["plant"]
        gt_disease = sample["disease"]
        gt_status = sample["status"]

        # Check matches
        plant_match = plant_type.lower() in gt_plant.lower() or gt_plant.lower() in plant_type.lower()

        if gt_disease.lower() == "healthy":
            disease_match = adapter.is_healthy(raw_class)
        else:
            disease_words = gt_disease.lower().replace(" ", "_").split("_")
            disease_match = any(word in raw_class.lower() for word in disease_words if len(word) > 2)

        status_match = adapter.is_healthy(raw_class) == (gt_status == "healthy")
        perfect_match = plant_match and disease_match and status_match

        # Count matches
        if perfect_match:
            perfect_matches += 1
        if plant_match:
            plant_matches += 1
        if status_match:
            status_matches += 1

        # Icons
        perfect_icon = "🎯" if perfect_match else "❌"
        plant_icon = "🌿" if plant_match else "❌"
        status_icon = "💚" if status_match else "💔"

        results.append(
            {
                "filename": sample["filename"],
                "gt_plant": gt_plant,
                "gt_disease": gt_disease,
                "gt_status": gt_status,
                "pred_plant": plant_type,
                "pred_disease": readable_name,
                "pred_raw": raw_class,
                "confidence": confidence,
                "perfect_match": perfect_match,
                "plant_match": plant_match,
                "status_match": status_match,
            }
        )

        print(f"{perfect_icon} {sample['filename']} {plant_icon}{status_icon}")
        print(f"   GT: {gt_plant} - {gt_disease} ({gt_status})")
        print(f"   Pred: {plant_type} - {readable_name} ({confidence:.1%})")
        print()

    # Final statistics
    total = len(results)
    print("=" * 70)
    print("🏆 FINAL RESULTS")
    print("=" * 70)
    print(f"Total images tested: {total}")
    print(f"Perfect matches: {perfect_matches}/{total} ({perfect_matches / total:.1%})")
    print(f"Plant type correct: {plant_matches}/{total} ({plant_matches / total:.1%})")
    print(f"Health status correct: {status_matches}/{total} ({status_matches / total:.1%})")

    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    print(f"Average confidence: {avg_confidence:.1%}")

    # Plant-wise breakdown
    plant_stats = {}
    for result in results:
        plant = result["gt_plant"]
        if plant not in plant_stats:
            plant_stats[plant] = {"total": 0, "correct": 0}
        plant_stats[plant]["total"] += 1
        if result["perfect_match"]:
            plant_stats[plant]["correct"] += 1

    print("\n🌿 Plant-wise Performance:")
    print("-" * 40)
    for plant, stats in sorted(plant_stats.items()):
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        print(f"{plant:15} {stats['correct']:2}/{stats['total']:2} ({accuracy:.1%})")

    # Disease status breakdown
    healthy_results = [r for r in results if r["gt_status"] == "healthy"]
    diseased_results = [r for r in results if r["gt_status"] == "diseased"]

    healthy_correct = sum(1 for r in healthy_results if r["status_match"])
    diseased_correct = sum(1 for r in diseased_results if r["status_match"])

    print("\n🏥 Health Status Performance:")
    print("-" * 40)
    if healthy_results:
        print(f"Healthy plants:  {healthy_correct:2}/{len(healthy_results):2} ({healthy_correct / len(healthy_results):.1%})")
    if diseased_results:
        print(f"Diseased plants: {diseased_correct:2}/{len(diseased_results):2} ({diseased_correct / len(diseased_results):.1%})")

    print("\n🎉 CONCLUSION:")
    if perfect_matches == total:
        print("🥇 PERFECT SCORE! Your model achieved 100% accuracy!")
        print("   This Hugging Face model is ready for production use.")
    elif perfect_matches >= total * 0.9:
        print("🥈 EXCELLENT! Over 90% accuracy - great for real-world use.")
    elif perfect_matches >= total * 0.8:
        print("🥉 GOOD! Over 80% accuracy - suitable for most applications.")
    else:
        print("📈 NEEDS IMPROVEMENT - Consider trying other models or fine-tuning.")

    print("\n💡 Model Details:")
    print(f"   Model: {adapter.model_name}")
    print("   Type: Vision Transformer (ViT)")
    print(f"   Classes: {len(adapter.class_names)}")
    print(f"   Device: {adapter.device}")


def main() -> None:
    comprehensive_test()


if __name__ == "__main__":
    main()
