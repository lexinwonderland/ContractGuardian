from typing import Tuple
import io
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image


def extract_text_from_pdf_bytes(data: bytes) -> Tuple[str, bool]:
	"""Return (text, used_ocr). Attempts text extraction first; OCR fallback if needed."""
	text = ""
	used_ocr = False
	# Try fast extract via PyPDF2
	try:
		reader = PdfReader(io.BytesIO(data))
		pages_text = []
		for page in reader.pages:
			pages_text.append(page.extract_text() or "")
		text = "\n".join(pages_text)
	except Exception:
		text = ""

	if text and text.strip():
		return text, used_ocr

	# Try pdfminer (more robust)
	try:
		text = pdfminer_extract_text(io.BytesIO(data)) or ""
	except Exception:
		text = ""

	if text and text.strip():
		return text, used_ocr

	# OCR fallback
	images = convert_from_bytes(data, dpi=300)
	ocr_text_parts = []
	for img in images:
		ocr_text_parts.append(pytesseract.image_to_string(img))
	used_ocr = True
	return "\n".join(ocr_text_parts), used_ocr


def extract_text_from_image_bytes(data: bytes) -> str:
	img = Image.open(io.BytesIO(data))
	return pytesseract.image_to_string(img) 