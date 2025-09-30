# Contract Guardian

Contract storage, scanning (OCR), and plain‑language alerts for performers.

## Features
- Flag predatory/problematic language with clear explanations and next‑step guidance
- Structured contract storage with search and timelines
- PDF/image text extraction with OCR fallback

## Tech
- FastAPI + Uvicorn
- SQLite (via SQLAlchemy)
- Basic HTML templates (Jinja2)
- OCR via Tesseract (optional but recommended)

## Setup
1. Python 3.11+
2. Install system deps
   - macOS (Homebrew):
     - Tesseract: `brew install tesseract`
     - Poppler (for PDF rendering when OCR fallback is used): `brew install poppler`
   - Ubuntu/Debian:
     - `sudo apt update && sudo apt install -y tesseract-ocr poppler-utils`
   - Fedora:
     - `sudo dnf install -y tesseract tesseract-langpack-eng poppler-utils`
3. Create venv and install Python deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -3.11 -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Windows (CMD):

```bat
py -3.11 -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000`.

## Deploy (Docker)
Build and run locally with Docker:

```bash
docker build -t contract-guardian .
docker run --rm -p 8000:8000 \
  -e CG_SECRET_KEY="PedKcsPs6dNNeGDfDYUBBB9FYFhGSAWLavPVrgBPazJgDOonJ52GjloFrvA0GK7S" \
  -e CG_COOKIE_SECURE=1 \
  -e CG_COOKIE_SAMESITE=lax \
  contract-guardian
```

For cloud platforms (Render, Fly.io, Railway, etc.), use the included Dockerfile. For platforms that use Procfile (Heroku-like):

```
web: gunicorn -k uvicorn.workers.UvicornWorker -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-8000} app.main:app
```

### Environment variables
- `CG_SECRET_KEY` (required in production): JWT signing key
- `CG_COOKIE_SECURE` (default: 0): set to `1` in production
- `CG_COOKIE_SAMESITE` (default: `lax`): `lax|strict|none`
- `CG_COOKIE_DOMAIN` (optional): cookie domain like `.example.com`

## Notes
- If a PDF has extractable text, OCR is skipped. Otherwise pages are rasterized and sent to Tesseract.
- Flags are heuristic, not legal advice. Always consult a qualified attorney. 