from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database import engine, Base
from routes import password, auth

app = FastAPI()

# 🔒 Obsługa CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tworzenie tabel w bazie
Base.metadata.create_all(bind=engine)

# Rejestracja routerów API
app.include_router(auth.router)
app.include_router(password.router)

# Serowanie frontendu ze statycznych plików
frontend_path = Path(__file__).parent.parent / "frontend" / "frontend-app" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")


