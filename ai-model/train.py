"""
Plant Disease Detection Model — Training Script

Trains a MobileNetV2-based CNN on the PlantVillage dataset for leaf disease
classification.  Uses transfer learning with fine-tuning for best accuracy.

Usage:
    1. Download the PlantVillage dataset from Kaggle.
    2. Extract it so that `dataset/` contains one subfolder per class,
       e.g.  dataset/Tomato___Early_blight/  , dataset/Tomato___healthy/ , …
    3. Run:  python train.py

The trained model and class-name list will be saved under  saved_model/ .
"""

import os
import json
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, Model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ─── Configuration ────────────────────────────────────────────────────────────

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
SAVED_MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_model")
MODEL_PATH = os.path.join(SAVED_MODEL_DIR, "plant_disease_model.h5")
CLASS_NAMES_PATH = os.path.join(SAVED_MODEL_DIR, "class_names.json")
HISTORY_PLOT_PATH = os.path.join(SAVED_MODEL_DIR, "training_history.png")

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS_TRANSFER = 10   # Initial training (frozen base)
EPOCHS_FINETUNE = 5    # Fine-tuning (unfrozen top layers)
LEARNING_RATE = 1e-4


def main():
    os.makedirs(SAVED_MODEL_DIR, exist_ok=True)

    if not os.path.isdir(DATASET_DIR):
        print(f"ERROR: Dataset directory not found at {DATASET_DIR}")
        print("Please download the PlantVillage dataset from Kaggle and extract")
        print("it into  ai-model/dataset/  with one subfolder per class.")
        return

    # ── Data Generators (with augmentation) ───────────────────────────────

    print("Loading dataset …")

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
        rotation_range=25,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode="nearest",
    )

    train_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )

    val_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    num_classes = train_generator.num_classes
    class_names = list(train_generator.class_indices.keys())
    print(f"Found {num_classes} classes: {class_names[:5]} …")

    # Save class names for inference
    with open(CLASS_NAMES_PATH, "w") as f:
        json.dump(class_names, f, indent=2)

    # ── Build MobileNetV2 Model ───────────────────────────────────────────

    print("Building MobileNetV2 model …")

    base_model = MobileNetV2(
        weights="imagenet",
        include_top=False,
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )
    base_model.trainable = False  # Freeze during transfer learning phase

    x = base_model.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    predictions = layers.Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=predictions)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.summary()

    # ── Phase 1: Transfer Learning ────────────────────────────────────────

    print(f"\n{'='*60}")
    print(f"Phase 1: Transfer Learning ({EPOCHS_TRANSFER} epochs)")
    print(f"{'='*60}\n")

    history1 = model.fit(
        train_generator,
        epochs=EPOCHS_TRANSFER,
        validation_data=val_generator,
    )

    # ── Phase 2: Fine-tuning ──────────────────────────────────────────────

    print(f"\n{'='*60}")
    print(f"Phase 2: Fine-tuning ({EPOCHS_FINETUNE} epochs)")
    print(f"{'='*60}\n")

    # Unfreeze top layers of the base model for fine-tuning
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE / 10),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history2 = model.fit(
        train_generator,
        epochs=EPOCHS_FINETUNE,
        validation_data=val_generator,
    )

    # ── Save Model ────────────────────────────────────────────────────────

    model.save(MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    # ── Plot Training History ─────────────────────────────────────────────

    acc = history1.history["accuracy"] + history2.history["accuracy"]
    val_acc = history1.history["val_accuracy"] + history2.history["val_accuracy"]
    loss = history1.history["loss"] + history2.history["loss"]
    val_loss = history1.history["val_loss"] + history2.history["val_loss"]

    epochs_range = range(1, len(acc) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(epochs_range, acc, label="Training Accuracy")
    ax1.plot(epochs_range, val_acc, label="Validation Accuracy")
    ax1.set_title("Model Accuracy")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Accuracy")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(epochs_range, loss, label="Training Loss")
    ax2.plot(epochs_range, val_loss, label="Validation Loss")
    ax2.set_title("Model Loss")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Loss")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(HISTORY_PLOT_PATH, dpi=150)
    print(f"Training history plot saved to {HISTORY_PLOT_PATH}")
    print("\nTraining complete! ✅")


if __name__ == "__main__":
    main()
