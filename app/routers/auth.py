from fastapi import APIRouter, Depends, HTTPException, Response, Form
import os
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..auth import hash_password, verify_password, create_access_token, COOKIE_NAME

router = APIRouter()

# Cookie/security settings configurable via environment for production deploys
# Defaults are safe for local dev; override in production:
#   CG_COOKIE_SECURE=1 (sets Secure flag)
#   CG_COOKIE_SAMESITE=lax|strict|none
#   CG_COOKIE_DOMAIN=.yourdomain.com (optional)
_SECURE_DEFAULT = "0"  # local default
COOKIE_SECURE = os.environ.get("CG_COOKIE_SECURE", _SECURE_DEFAULT) in ("1", "true", "True")
COOKIE_SAMESITE = os.environ.get("CG_COOKIE_SAMESITE", "lax")
COOKIE_DOMAIN = os.environ.get("CG_COOKIE_DOMAIN") or None


@router.post("/register")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
	email = (email or '').strip().lower()
	if not email or not password:
		raise HTTPException(status_code=400, detail="Email and password required")
	if db.query(models.User).filter_by(email=email).first():
		raise HTTPException(status_code=400, detail="Email already registered")
	pwd_hash, salt = hash_password(password)
	user = models.User(email=email, password_hash=pwd_hash, password_salt=salt)
	db.add(user)
	db.commit()
	db.refresh(user)
	return {"id": user.id, "email": user.email}


@router.post("/login")
def login(response: Response, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
	user = db.query(models.User).filter_by(email=(email or '').strip().lower()).first()
	if not user or not verify_password(password, user.password_hash, user.password_salt):
		raise HTTPException(status_code=401, detail="Invalid credentials")
	token = create_access_token(user.id)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
        max_age=60*60*24*7,
    )
	return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    # Mirror cookie attributes to ensure deletion across browsers
    response.delete_cookie(
        COOKIE_NAME,
        domain=COOKIE_DOMAIN,
        samesite=COOKIE_SAMESITE,
    )
	return {"ok": True}


@router.get("/whoami")
def whoami(db: Session = Depends(get_db)):
	# Minimal; clients should use protected endpoints to verify auth
	return {"ok": True} 