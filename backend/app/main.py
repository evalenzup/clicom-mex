from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.estaciones import router as estaciones_router

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir a ["http://localhost:5173"] si lo prefieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(estaciones_router)
