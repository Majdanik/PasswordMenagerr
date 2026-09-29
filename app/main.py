from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from pathlib import Path
import os
import uvicorn
from app.database import engine, Base, ensure_user_security_columns
from app.routes import password, auth, vault

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Normalizuje odpowiedź walidacji Pydantic (domyślnie lista obiektów) do
    # pojedynczego stringa - spójnie z resztą API, gdzie `detail` to zawsze string.
    message = exc.errors()[0]["msg"]
    if message.startswith("Value error, "):
        message = message[len("Value error, "):]
    return JSONResponse(status_code=422, content={"detail": message})

# 🔒 Obsługa CORS
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response: Response = await call_next(request)

    csp_policy = os.getenv(
        "CONTENT_SECURITY_POLICY",
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'",
    )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = csp_policy

    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

# Tworzenie tabel w bazie
Base.metadata.create_all(bind=engine)
ensure_user_security_columns()

# Rejestracja routerów API
app.include_router(auth.router)
app.include_router(password.router)
app.include_router(vault.router)

# Serowanie frontendu ze statycznych plików
frontend_path = Path(__file__).parent.parent / "frontend" / "frontend-app" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


