from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from .estaciones import router as estaciones_router

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir a ["http://localhost:5173"] si lo prefieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data: *.tile.openstreetmap.org server.arcgisonline.com cartodb-basemaps-a.global.ssl.fastly.net *.tile.opentopomap.org; connect-src 'self' https://localhost;"
    return response

# Rutas de la API
app.include_router(estaciones_router, prefix="/api")

# --- MONTAJE ROBUSTO DE ARCHIVOS ESTÁTICOS ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists() and STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    print(f"[INFO] Sirviendo archivos estáticos desde: {STATIC_DIR}")
else:
    print(f"[WARN] El directorio de estáticos NO existe: {STATIC_DIR}. No se montarán archivos estáticos.")