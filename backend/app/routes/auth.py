"""
Authentication routes: register, login, profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Farmer
from app.schemas.schemas import (
    FarmerRegister,
    FarmerLogin,
    FarmerProfile,
    FarmerUpdate,
    Token,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_farmer,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=FarmerProfile, status_code=status.HTTP_201_CREATED)
def register(payload: FarmerRegister, db: Session = Depends(get_db)):
    """Register a new farmer account."""
    # Check if phone number already exists
    existing = db.query(Farmer).filter(Farmer.phone == payload.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    farmer = Farmer(
        name=payload.name,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        village=payload.village,
        district=payload.district,
        state=payload.state,
        language=payload.language,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer


@router.post("/login", response_model=Token)
def login(payload: FarmerLogin, db: Session = Depends(get_db)):
    """Authenticate a farmer and return a JWT token."""
    farmer = db.query(Farmer).filter(Farmer.phone == payload.phone).first()
    if not farmer or not verify_password(payload.password, farmer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    access_token = create_access_token(data={"sub": str(farmer.id)})
    return Token(access_token=access_token)


@router.get("/profile", response_model=FarmerProfile)
def get_profile(current_farmer: Farmer = Depends(get_current_farmer)):
    """Get the profile of the currently authenticated farmer."""
    return current_farmer


@router.put("/profile", response_model=FarmerProfile)
def update_profile(
    payload: FarmerUpdate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Update the profile of the currently authenticated farmer."""
    if payload.name is not None:
        current_farmer.name = payload.name
    if payload.village is not None:
        current_farmer.village = payload.village
    if payload.district is not None:
        current_farmer.district = payload.district
    if payload.state is not None:
        current_farmer.state = payload.state
    if payload.language is not None:
        current_farmer.language = payload.language

    db.commit()
    db.refresh(current_farmer)
    return current_farmer
