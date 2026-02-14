import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.utils.security import verify_password
from app.utils.security import hash_password

router = APIRouter()

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already Registered"
        )

    if len(user.password) < 6: 
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )
    hashed_password = hash_password(user.password)
    otp = str(random.randint(100000, 999999))

    new_user = models.User(
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_password,
        is_verified=False,
        otp=otp
    )
    db.add(new_user)
    db.commit()
    print("User OTP:", otp)
    db.refresh(new_user)

    return {"message": "User created successfully"}

@router.post("/login")
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=404, 
            detail="User not found")

    if not verify_password(login_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401, 
            detail="Incorrect password")

    return {"message": "Login successful"}


@router.post("/verify")
def verify_user(data: schemas.VerifyUser, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not Found"
        )

    if user.is_verified:
        return {"message": "User Already Verified"}
        #Proper edge case senario to prevent dual verification
    if user.otp != data.otp:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    
    user.is_verified = True
    user.otp = None
    db.commit()
    return {"message": "ACCOUNT VERIFICATION SUCCESSFUL"}