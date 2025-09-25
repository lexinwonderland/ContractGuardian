from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from .database import init_db
from .routers import contracts, auth
from .auth import get_current_user
from fastapi import HTTPException

app = FastAPI(title="Contract Guardian")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

async def get_auth_status(request: Request):
	"""Check if user is authenticated, return user if authenticated, None if not"""
	try:
		user = await get_current_user(request)
		return user
	except HTTPException:
		return None

@app.on_event("startup")
async def on_startup() -> None:
	init_db()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
	user = await get_auth_status(request)
	return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
	user = await get_auth_status(request)
	return templates.TemplateResponse("upload.html", {"request": request, "user": user})

@app.get("/contracts", response_class=HTMLResponse)
async def list_page(request: Request):
	# Thin wrapper around API list; template fetches client-side or we server-render minimal
	user = await get_auth_status(request)
	return templates.TemplateResponse("list.html", {"request": request, "user": user})

@app.get("/contracts/view/{contract_id}", response_class=HTMLResponse)
async def contract_view(contract_id: int, request: Request):
	user = await get_auth_status(request)
	return templates.TemplateResponse("contract.html", {"request": request, "contract_id": contract_id, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
	user = await get_auth_status(request)
	return templates.TemplateResponse("login.html", {"request": request, "user": user})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
	user = await get_auth_status(request)
	return templates.TemplateResponse("register.html", {"request": request, "user": user}) 