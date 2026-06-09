"""
Plant Disease Prediction — Inference Script

Standalone script to predict plant disease from a leaf image using the
trained MobileNetV2 model.

Usage:
    python predict.py <path_to_leaf_image>
"""

import os
import sys
import json
import numpy as np
from PIL import Image

SAVED_MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_model")
MODEL_PATH = os.path.join(SAVED_MODEL_DIR, "plant_disease_model.h5")
CLASS_NAMES_PATH = os.path.join(SAVED_MODEL_DIR, "class_names.json")
IMG_SIZE = 224


def load_model():
    """Load the trained Keras model and class name list."""
    import tensorflow as tf

    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("Run  python train.py  first to train the model.")
        sys.exit(1)

    model = tf.keras.models.load_model(MODEL_PATH)

    with open(CLASS_NAMES_PATH, "r") as f:
        class_names = json.load(f)

    return model, class_names


def predict(image_path: str, model, class_names: list) -> dict:
    """
    Predict disease from a leaf image.

    Args:
        image_path: Path to the leaf image file.
        model: Loaded Keras model.
        class_names: List of class labels.

    Returns:
        Dictionary with disease name, confidence, and top-3 predictions.
    """
    img = Image.open(image_path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)[0]
    top_indices = np.argsort(predictions)[::-1][:3]

    results = {
        "disease": class_names[top_indices[0]],
        "confidence": round(float(predictions[top_indices[0]]) * 100, 2),
        "top_3": [
            {
                "disease": class_names[idx],
                "confidence": round(float(predictions[idx]) * 100, 2),
            }
            for idx in top_indices
        ],
    }
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python predict.py <path_to_leaf_image>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"ERROR: Image not found at {image_path}")
        sys.exit(1)

    print("Loading model …")
    model, class_names = load_model()

    print(f"Predicting disease for: {image_path}")
    result = predict(image_path, model, class_names)

    print(f"\n{'='*50}")
    print(f"  Disease  : {result['disease']}")
    print(f"  Confidence: {result['confidence']}%")
    print(f"{'='*50}")
    print("\nTop 3 predictions:")
    for i, pred in enumerate(result["top_3"], 1):
        print(f"  {i}. {pred['disease']} — {pred['confidence']}%")


if __name__ == "__main__":
    main()
