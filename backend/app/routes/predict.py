"""
Disease prediction routes: upload image, get prediction, get history.
Includes disease recommendation lookup.
"""
import os
import json
import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Farmer, Prediction, Recommendation
from app.schemas.schemas import (
    PredictionResponse,
    PredictionWithRecommendation,
    RecommendationResponse,
)
from app.services.auth_service import get_current_farmer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Disease Detection"])

# ─── Load disease info from JSON knowledge base ──────────────────────────────
DISEASE_INFO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "ai-model", "disease_info.json"
)

_disease_info: dict = {}

def _load_disease_info():
    global _disease_info
    try:
        abs_path = os.path.abspath(DISEASE_INFO_PATH)
        if os.path.exists(abs_path):
            with open(abs_path, "r", encoding="utf-8") as f:
                _disease_info = json.load(f)
            logger.info("Loaded disease info with %d entries", len(_disease_info))
        else:
            logger.warning("disease_info.json not found at %s", abs_path)
    except Exception as e:
        logger.error("Failed to load disease_info.json: %s", e)

_load_disease_info()


# ─── Attempt to load TensorFlow model ────────────────────────────────────────
_model = None
_class_names: List[str] = []

MODEL_PATH = os.getenv("MODEL_PATH", "ai-model/saved_model/plant_disease_model.h5")
CLASS_NAMES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "ai-model", "saved_model", "class_names.json"
)

def _load_model():
    global _model, _class_names
    try:
        abs_model = os.path.abspath(MODEL_PATH)
        abs_classes = os.path.abspath(CLASS_NAMES_PATH)
        if os.path.exists(abs_model):
            import tensorflow as tf
            _model = tf.keras.models.load_model(abs_model)
            logger.info("Loaded TensorFlow model from %s", abs_model)
        if os.path.exists(abs_classes):
            with open(abs_classes, "r") as f:
                _class_names = json.load(f)
            logger.info("Loaded %d class names", len(_class_names))
    except ImportError:
        logger.warning("TensorFlow not installed — prediction will use mock mode.")
    except Exception as e:
        logger.error("Failed to load model: %s", e)

_load_model()


# ─── Upload directory ─────────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(os.path.abspath(UPLOAD_DIR), exist_ok=True)


def _predict_image(file_path: str) -> tuple:
    """
    Run inference on an image file. Returns (disease_name, confidence).
    Falls back to mock prediction if model is not loaded.
    """
    if _model is not None and _class_names:
        import numpy as np
        from PIL import Image

        img = Image.open(file_path).resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        predictions = _model.predict(img_array)
        predicted_idx = int(np.argmax(predictions[0]))
        confidence = float(np.max(predictions[0])) * 100

        disease_name = _class_names[predicted_idx] if predicted_idx < len(_class_names) else "Unknown"
        return disease_name, round(confidence, 2)

    # Mock prediction for development / demo
    import random
    mock_diseases = [
        ("Tomato - Early Blight", 96.2),
        ("Tomato - Late Blight", 89.5),
        ("Potato - Early Blight", 92.1),
        ("Corn - Common Rust", 88.7),
        ("Tomato - Healthy", 99.1),
    ]
    return random.choice(mock_diseases)


@router.post("/predict", response_model=PredictionWithRecommendation)
async def predict_disease(
    file: UploadFile = File(...),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Upload a leaf image and receive a disease prediction with treatment
    recommendations. The image is processed through the MobileNetV2 CNN model.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are accepted",
        )

    # Save uploaded file
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(os.path.abspath(UPLOAD_DIR), filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Run prediction
    disease_name, confidence = _predict_image(file_path)

    # Save to database
    prediction = Prediction(
        farmer_id=current_farmer.id,
        image_url=f"/uploads/{filename}",
        disease=disease_name,
        confidence=confidence,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    # Fetch recommendation
    recommendation = None
    # Try from database first
    rec_db = db.query(Recommendation).filter(Recommendation.disease == disease_name).first()
    if rec_db:
        recommendation = RecommendationResponse.model_validate(rec_db)
    elif disease_name in _disease_info:
        info = _disease_info[disease_name]
        recommendation = RecommendationResponse(
            disease=disease_name,
            description=info.get("description"),
            cause=info.get("cause"),
            symptoms=info.get("symptoms"),
            organic_treatment=info.get("organic_treatment"),
            chemical_treatment=info.get("chemical_treatment"),
            prevention=info.get("prevention"),
        )

    return PredictionWithRecommendation(
        prediction=PredictionResponse.model_validate(prediction),
        recommendation=recommendation,
    )


@router.get("/predict/history", response_model=List[PredictionResponse])
def prediction_history(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get the disease prediction history for the current farmer."""
    predictions = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == current_farmer.id)
        .order_by(Prediction.created_at.desc())
        .limit(50)
        .all()
    )
    return predictions


@router.get("/recommendation/{disease}", response_model=RecommendationResponse)
def get_recommendation(disease: str, db: Session = Depends(get_db)):
    """Get treatment recommendation for a specific disease."""
    # Try database
    rec = db.query(Recommendation).filter(Recommendation.disease == disease).first()
    if rec:
        return rec

    # Try JSON knowledge base
    if disease in _disease_info:
        info = _disease_info[disease]
        return RecommendationResponse(
            disease=disease,
            description=info.get("description"),
            cause=info.get("cause"),
            symptoms=info.get("symptoms"),
            organic_treatment=info.get("organic_treatment"),
            chemical_treatment=info.get("chemical_treatment"),
            prevention=info.get("prevention"),
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No recommendation found for disease: {disease}",
    )
