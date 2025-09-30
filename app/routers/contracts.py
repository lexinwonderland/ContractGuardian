from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import os
from fastapi.responses import FileResponse
from ..database import get_db
from .. import models, schemas
from ..ocr import extract_text_from_pdf_bytes, extract_text_from_image_bytes
from ..analyzer import analyze_text
from ..auth import get_current_user

router = APIRouter()

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=schemas.ContractRead)
async def upload_contract(
	title: str = Form(...),
	counterparty: Optional[str] = Form(None),
	production: Optional[str] = Form(None),
	contract_date: Optional[date] = Form(None),
	file: UploadFile = File(...),
	db: Session = Depends(get_db),
	user: models.User = Depends(get_current_user),
):
	# Size limit protection
	if file.size and file.size > MAX_UPLOAD_BYTES:
		raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
	filename = file.filename or "uploaded"
	data = await file.read()
	if len(data) > MAX_UPLOAD_BYTES:
		raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
	text = ""
	stored_filename = None

	content_type = file.content_type or ""
	try:
		if content_type in ("application/pdf",) or filename.lower().endswith(".pdf"):
			text, _ = extract_text_from_pdf_bytes(data)
		elif content_type.startswith("image/"):
			text = extract_text_from_image_bytes(data)
		else:
			# Assume text
			text = data.decode("utf-8", errors="ignore")
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Failed to extract text: {e}")

	if not text or not text.strip():
		raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

	try:
		stored_filename = os.path.join(UPLOAD_DIR, filename)
		with open(stored_filename, "wb") as f:
			f.write(data)

		flags = analyze_text(text)

		contract = models.Contract(
			title=title,
			counterparty=counterparty,
			production=production,
			contract_date=contract_date,
			stored_filename=stored_filename,
			text=text,
			user_id=user.id,
		)
		db.add(contract)
		db.flush()

		for flag in flags:
			cf = models.ClauseFlag(contract_id=contract.id, **flag)
			db.add(cf)

		db.commit()
		db.refresh(contract)
		return contract
	except Exception as e:
		# Surface error details to client and logs to aid debugging on Render (avoid 502 with no message)
		try:
			print(f"Upload processing error: {e}")
		except Exception:
			pass
		raise HTTPException(status_code=500, detail=f"Server error during upload: {e}")


@router.post("/create", response_model=schemas.ContractRead)
async def create_contract(
	payload: schemas.ContractCreate,
	db: Session = Depends(get_db),
	user: models.User = Depends(get_current_user),
):
	flags = analyze_text(payload.text)
	contract = models.Contract(
		title=payload.title,
		counterparty=payload.counterparty,
		production=payload.production,
		contract_date=payload.contract_date,
		stored_filename=payload.stored_filename,
		text=payload.text,
		user_id=user.id,
	)
	db.add(contract)
	db.flush()
	for flag in flags:
		db.add(models.ClauseFlag(contract_id=contract.id, **flag))
	db.commit()
	db.refresh(contract)
	return contract


@router.get("/list", response_model=List[schemas.ContractListItem])
async def list_contracts(
	q: Optional[str] = None,
	db: Session = Depends(get_db),
	user: models.User = Depends(get_current_user),
):
	query = db.query(models.Contract).filter(models.Contract.user_id == user.id)
	if q:
		like = f"%{q}%"
		query = query.filter((models.Contract.title.ilike(like)) | (models.Contract.text.ilike(like)))
	query = query.order_by(models.Contract.contract_date.desc().nullslast(), models.Contract.created_at.desc())
	rows = query.all()
	return rows


@router.get("/{contract_id}", response_model=schemas.ContractRead)
async def get_contract(contract_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
	contract = db.query(models.Contract).filter_by(id=contract_id, user_id=user.id).first()
	if not contract:
		raise HTTPException(status_code=404, detail="Not found")
	return contract


@router.delete("/{contract_id}")
async def delete_contract(contract_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
	contract = db.query(models.Contract).filter_by(id=contract_id, user_id=user.id).first()
	if not contract:
		raise HTTPException(status_code=404, detail="Not found")
	stored_path = contract.stored_filename
	# Delete DB record (flags cascade via relationship)
	db.delete(contract)
	db.commit()
	# Safely remove uploaded file if it exists and is within the uploads directory
	try:
		if stored_path and os.path.isfile(stored_path):
			uploads_abs = os.path.abspath(UPLOAD_DIR)
			file_abs = os.path.abspath(stored_path)
			if os.path.commonpath([uploads_abs, file_abs]) == uploads_abs:
				os.remove(file_abs)
	except Exception:
		# Ignore file delete errors to avoid masking API success
		pass
	return {"ok": True}


@router.get("/file/{contract_id}")
async def get_contract_file(contract_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
	contract = db.query(models.Contract).filter_by(id=contract_id, user_id=user.id).first()
	if not contract or not contract.stored_filename or not os.path.isfile(contract.stored_filename):
		raise HTTPException(status_code=404, detail="File not found")
	return FileResponse(path=contract.stored_filename) 