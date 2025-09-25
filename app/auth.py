import os
import hashlib
import hmac
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Request
import jwt
from .database import SessionLocal
from . import models

SECRET_KEY = os.environ.get("CG_SECRET_KEY", "dev-secret-change-me")
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
COOKIE_NAME = "access_token"


def _pbkdf2_hash(password: str, salt: str) -> str:
	return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()


def hash_password(password: str) -> tuple[str, str]:
	salt = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
	pwd_hash = _pbkdf2_hash(password, salt)
	return pwd_hash, salt


def verify_password(password: str, password_hash: str, password_salt: str) -> bool:
	calc = _pbkdf2_hash(password, password_salt)
	return hmac.compare_digest(calc, password_hash)


def create_access_token(user_id: int) -> str:
	exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	payload = {"sub": str(user_id), "exp": exp}
	return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALG)


def decode_access_token(token: str) -> Optional[int]:
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALG])
		return int(payload.get("sub"))
	except Exception:
		return None


async def get_current_user(request: Request) -> models.User:
	token = request.cookies.get(COOKIE_NAME)
	if not token:
		raise HTTPException(status_code=401, detail="Not authenticated")
	user_id = decode_access_token(token)
	if not user_id:
		raise HTTPException(status_code=401, detail="Invalid token")
	db = SessionLocal()
	try:
		user = db.query(models.User).filter_by(id=user_id).first()
		if not user:
			raise HTTPException(status_code=401, detail="User not found")
		return user
	finally:
		db.close() 