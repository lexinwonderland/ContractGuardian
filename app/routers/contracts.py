from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import os
import time
import uuid
import asyncio
import psutil
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
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/bmp",
    "text/plain", "text/csv"
}


async def _extract_text_with_timeout(data: bytes, content_type: str, filename: str):
	"""Extract text from file data with proper error handling"""
	if content_type in ("application/pdf",) or filename.lower().endswith(".pdf"):
		return extract_text_from_pdf_bytes(data)
	elif content_type.startswith("image/"):
		return extract_text_from_image_bytes(data)
	else:
		# Assume text
		return data.decode("utf-8", errors="ignore"), None


async def _analyze_text_with_timeout(text: str):
	"""Analyze text with proper error handling"""
	return analyze_text(text)


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
	request_id = str(uuid.uuid4())[:8]
	start_time = time.time()
	
	try:
		# Log request start
		print(f"[{request_id}] Upload started - User: {user.id}, File: {file.filename}, Size: {file.size}")
		
		# Early size validation
		if file.size and file.size > MAX_UPLOAD_BYTES:
			print(f"[{request_id}] File too large: {file.size} bytes")
			raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
		
		# Content type validation
		content_type = file.content_type or ""
		if content_type not in ALLOWED_CONTENT_TYPES and not any(filename.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.txt', '.csv']):
			print(f"[{request_id}] Unsupported content type: {content_type}")
			raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
		
		# Read file data
		filename = file.filename or "uploaded"
		print(f"[{request_id}] Reading file data...")
		data = await file.read()
		
		if len(data) > MAX_UPLOAD_BYTES:
			print(f"[{request_id}] File too large after read: {len(data)} bytes")
			raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
		
		print(f"[{request_id}] File read complete: {len(data)} bytes, Memory: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB")
		
		# Text extraction with timeout
		text = ""
		stored_filename = None
		
		print(f"[{request_id}] Starting text extraction...")
		extraction_start = time.time()
		
		try:
			# Add timeout for text extraction
			extraction_task = asyncio.create_task(_extract_text_with_timeout(data, content_type, filename))
			text, _ = await asyncio.wait_for(extraction_task, timeout=60.0)  # 60 second timeout
			
			extraction_time = time.time() - extraction_start
			print(f"[{request_id}] Text extraction complete in {extraction_time:.2f}s, extracted {len(text)} chars")
			
		except asyncio.TimeoutError:
			print(f"[{request_id}] Text extraction timed out after 60s")
			raise HTTPException(status_code=408, detail="Text extraction timed out. Please try a smaller file.")
		except Exception as e:
			print(f"[{request_id}] Text extraction failed: {str(e)}")
			raise HTTPException(status_code=400, detail=f"Failed to extract text: {str(e)}")

		if not text or not text.strip():
			print(f"[{request_id}] No text extracted from file")
			raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

		# File saving with error handling
		print(f"[{request_id}] Saving file to disk...")
		try:
			stored_filename = filename
			full_path = os.path.join(UPLOAD_DIR, filename)
			
			# Ensure upload directory exists
			os.makedirs(UPLOAD_DIR, exist_ok=True)
			
			with open(full_path, "wb") as f:
				f.write(data)
			
			print(f"[{request_id}] File saved successfully: {os.path.isfile(full_path)}")
		except Exception as e:
			print(f"[{request_id}] File save failed: {str(e)}")
			raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

		# Text analysis with timeout
		print(f"[{request_id}] Starting text analysis...")
		analysis_start = time.time()
		
		try:
			# Limit text size for analysis to prevent memory issues
			analysis_text = text[:50000] if len(text) > 50000 else text
			if len(text) > 50000:
				print(f"[{request_id}] Text truncated to 50k chars for analysis (original: {len(text)} chars)")
			
			analysis_task = asyncio.create_task(_analyze_text_with_timeout(analysis_text))
			flags = await asyncio.wait_for(analysis_task, timeout=30.0)  # 30 second timeout
			
			analysis_time = time.time() - analysis_start
			print(f"[{request_id}] Analysis complete in {analysis_time:.2f}s, found {len(flags)} flags")
			
		except asyncio.TimeoutError:
			print(f"[{request_id}] Analysis timed out after 30s")
			raise HTTPException(status_code=408, detail="Text analysis timed out. Please try a smaller file.")
		except Exception as e:
			print(f"[{request_id}] Analysis failed: {str(e)}")
			raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

		# Database operations with transaction safety
		print(f"[{request_id}] Saving to database...")
		try:
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
			
			total_time = time.time() - start_time
			print(f"[{request_id}] Upload complete in {total_time:.2f}s, Memory: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB")
			
			return contract
			
		except Exception as e:
			print(f"[{request_id}] Database error: {str(e)}")
			db.rollback()
			raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
			
	except HTTPException:
		# Re-raise HTTP exceptions as-is
		raise
	except Exception as e:
		# Catch any unexpected errors
		total_time = time.time() - start_time
		print(f"[{request_id}] Unexpected error after {total_time:.2f}s: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")


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
	stored_filename = contract.stored_filename
	# Delete DB record (flags cascade via relationship)
	db.delete(contract)
	db.commit()
	# Safely remove uploaded file if it exists and is within the uploads directory
	try:
		if stored_filename:
			full_path = os.path.join(UPLOAD_DIR, stored_filename)
			if os.path.isfile(full_path):
				uploads_abs = os.path.abspath(UPLOAD_DIR)
				file_abs = os.path.abspath(full_path)
				if os.path.commonpath([uploads_abs, file_abs]) == uploads_abs:
					os.remove(file_abs)
	except Exception:
		# Ignore file delete errors to avoid masking API success
		pass
	return {"ok": True}


@router.get("/file/{contract_id}")
async def get_contract_file(contract_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
	contract = db.query(models.Contract).filter_by(id=contract_id, user_id=user.id).first()
	if not contract or not contract.stored_filename:
		raise HTTPException(status_code=404, detail="File not found")
	
	# Construct full path from UPLOAD_DIR + filename
	full_path = os.path.join(UPLOAD_DIR, contract.stored_filename)
	
	# Debug logging for file serving issues
	print(f"Looking for file: {full_path}")
	print(f"UPLOAD_DIR: {UPLOAD_DIR}")
	print(f"stored_filename: {contract.stored_filename}")
	print(f"File exists: {os.path.isfile(full_path)}")
	
	if not os.path.isfile(full_path):
		raise HTTPException(status_code=404, detail=f"File not found at {full_path}")
	return FileResponse(path=full_path)


@router.patch("/{contract_id}/status", response_model=schemas.ContractRead)
async def update_contract_status(
	contract_id: int, 
	status_update: schemas.ContractStatusUpdate,
	db: Session = Depends(get_db), 
	user: models.User = Depends(get_current_user)
):
	contract = db.query(models.Contract).filter_by(id=contract_id, user_id=user.id).first()
	if not contract:
		raise HTTPException(status_code=404, detail="Contract not found")
	
	# Validate status
	valid_statuses = ["hold", "negotiating", "signed"]
	if status_update.status not in valid_statuses:
		raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
	
	contract.status = status_update.status
	contract.consent_notes = status_update.consent_notes
	db.commit()
	db.refresh(contract)
	return contract 