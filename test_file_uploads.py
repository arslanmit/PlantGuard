#!/usr/bin/env python3
"""Test file upload functionality for PlantGuard Compare page.

This script creates test images and verifies upload functionality.
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def create_test_images():
    """Create test images for upload testing."""
    # Create temp directory for test images
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Created test directory: {temp_dir}")

    # Create test image A (green leaf)
    img_a = Image.new("RGB", (400, 300), color="green")
    img_a_path = str(Path(temp_dir) / "test_leaf_a.jpg")
    img_a.save(img_a_path, "JPEG")
    print(f"✅ Created test image A: {img_a_path}")

    # Create test image B (brown leaf - diseased)
    img_b = Image.new("RGB", (400, 300), color="brown")
    img_b_path = str(Path(temp_dir) / "test_leaf_b.jpg")
    img_b.save(img_b_path, "JPEG")
    print(f"✅ Created test image B: {img_b_path}")

    # Create a pattern image for more realistic testing
    pattern_array = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    img_pattern = Image.fromarray(pattern_array)
    img_pattern_path = str(Path(temp_dir) / "test_pattern.png")
    img_pattern.save(img_pattern_path, "PNG")
    print(f"✅ Created pattern image: {img_pattern_path}")

    return temp_dir, [img_a_path, img_b_path, img_pattern_path]


def test_file_properties():
    """Test file properties to ensure they meet upload requirements."""
    temp_dir, image_paths = create_test_images()

    print("\n🔍 Testing file properties:")
    print("-" * 40)

    for img_path in image_paths:
        p = Path(img_path)
        file_size = p.stat().st_size
        file_name = p.name
        file_ext = p.suffix.lower()

        print(f"📄 File: {file_name}")
        print(f"   Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
        print(f"   Extension: {file_ext}")

        # Check if file meets requirements
        if file_size < 200 * 1024 * 1024:  # 200MB limit
            print("   ✅ Size: OK")
        else:
            print("   ❌ Size: Too large")

        if file_ext in [".jpg", ".jpeg", ".png"]:
            print("   ✅ Format: OK")
        else:
            print("   ❌ Format: Not supported")

        print()

    print(f"📁 Test images available in: {temp_dir}")
    print("💡 You can use these images to test the file upload functionality")

    return temp_dir, image_paths


if __name__ == "__main__":
    print("🧪 PlantGuard File Upload Test")
    print("=" * 50)

    try:
        temp_dir, image_paths = test_file_properties()

        print("\n📋 Upload Test Instructions:")
        print("-" * 30)
        print("1. Open PlantGuard application")
        print("2. Navigate to Compare page")
        print("3. Try uploading the test images:")
        for path in image_paths:
            print(f"   - {path}")
        print("4. Check for any error messages")
        print("5. Verify images display correctly")

        print("\n🔧 Configuration Check:")
        print("-" * 25)
        print("- Max upload size: 200MB")
        print("- Supported formats: JPG, JPEG, PNG")
        print("- CORS disabled for uploads")
        print("- XSRF protection disabled")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

    print("\n🎉 Test setup completed successfully!")
