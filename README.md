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

## API

### `POST /contracts/analyze`
Authenticated endpoint that accepts a multipart form upload, runs OCR/text extraction, and streams the text through the ContractGuardian analyzer without saving anything to the database. This is useful when you only need a verdict from ContractGuardianGPT but do not want to keep the document on the platform.

Form fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | File | ✅ | PDF, image, or plain-text documents up to 10 MB. OCR is triggered automatically for images/PDFs that lack extractable text. |
| `title` | Text | ❌ | Optional context echoed back in the response. |
| `counterparty` | Text | ❌ | Optional producer/person name. |
| `production` | Text | ❌ | Optional show or production identifier. |
| `contract_date` | Date | ❌ | Optional ISO date string. |

Successful responses return JSON shaped like:

```json
{
  "title": "Sample Contract",
  "char_count": 12345,
  "truncated_for_analysis": false,
  "used_ocr": true,
  "extraction_seconds": 2.41,
  "analysis_seconds": 4.03,
  "flags": [
    {
      "category": "Exclusivity",
      "severity": "high",
      "excerpt": "Performer grants exclusive rights…",
      "explanation": "Explains why the clause is risky",
      "guidance": "Suggested negotiation language",
      "start_index": 102,
      "end_index": 182
    }
  ],
  "extracted_text_preview": "First 1,000 characters of extracted text…"
}
```

Example `curl` request (after authenticating and storing the session cookie in `cookie.txt`):

```bash
curl -X POST \
  -b cookie.txt \
  -F "file=@/path/to/contract.pdf" \
  -F "title=Sample Contract" \
  https://your-app.example.com/contracts/analyze
```

### `POST /contracts/upload`
Accepts the same multipart payload as `/contracts/analyze` but persists the contract, extracted text, and detected flags to the database so they appear in the dashboard. This is the endpoint used by the built-in upload form.

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
- `CONTRACTGUARDIAN_GPT_API_URL` (optional): HTTPS endpoint for ContractGuardianGPT analysis
- `CONTRACTGUARDIAN_GPT_API_KEY` (optional): Bearer token sent to the ContractGuardianGPT API
- `CONTRACTGUARDIAN_GPT_TIMEOUT` (optional, default `30` seconds): request timeout for the API

If the GPT API variables are not set (or the request fails), the app falls back to the built-in
rule-based analyzer so uploads continue to succeed.

## Notes
- If a PDF has extractable text, OCR is skipped. Otherwise pages are rasterized and sent to Tesseract.
- Flags are heuristic, not legal advice. Always consult a qualified attorney. 