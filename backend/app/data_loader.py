"""
Módulo para cargar y procesar todos los datos al inicio de la aplicación.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging
from . import store

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rutas base
DATA_DIR = Path(__file__).parent / "data"
JSON_DIR = DATA_DIR / "json"
CSV_DIR = DATA_DIR / "csv"

def load_station_catalog():
    """Carga el catálogo de estaciones desde los archivos JSON."""
    logger.info("Cargando catálogo de estaciones...")
    catalogs = []
    for json_file in JSON_DIR.glob("*_catalogo_estaciones_climatologicas.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            catalogs.extend(json.load(f))
    store.STATION_CATALOG = catalogs
    logger.info(f"Catálogo de estaciones cargado con {len(catalogs)} registros.")

def load_states_catalog():
    """Carga el catálogo de estados de México."""
    logger.info("Cargando catálogo de estados...")
    estados_path = JSON_DIR / "estados_mexico_catalogo.json"
    with open(estados_path, "r", encoding="utf-8") as f:
        store.STATES_CATALOG = json.load(f)
    logger.info("Catálogo de estados cargado.")

def load_station_data(station_id: str):
    """
    Carga y procesa los datos de una estación específica desde su archivo CSV.
    """
    logger.info(f"Cargando datos para la estación {station_id}...")
    
    # El patrón de búsqueda distingue entre IDs numéricos y alfanuméricos
    pattern = f"dia{station_id}.csv" if not station_id.isnumeric() else f"dia0{station_id}.csv"
    
    csv_files = list(CSV_DIR.rglob(pattern))
    
    if not csv_files:
        logger.error(f"No se encontró el archivo CSV para la estación {station_id} con el patrón {pattern}")
        return None

    csv_file = csv_files[0]
    logger.info(f"Archivo encontrado: {csv_file}")

    try:
        df = pd.read_csv(csv_file, encoding="utf-8").dropna(how="all")

        if "Fecha" not in df.columns:
            logger.warning(f"Archivo sin columna 'Fecha': {csv_file}")
            return None

        # Limpieza y formateo
        df = df.replace({np.nan: None})
        
        # Extraer variables y periodo
        variables = list(df.columns.drop("Fecha"))
        periodo = {
            "inicio": df["Fecha"].iloc[0] if not df.empty else None,
            "fin": df["Fecha"].iloc[-1] if not df.empty else None,
        }

        station_data = {
            "variables": variables,
            "periodo": periodo,
            "datos": df.to_dict(orient="records"),
        }
        
        store.STATION_DATA[station_id] = station_data
        logger.info(f"Datos de la estación {station_id} cargados en memoria.")
        return station_data

    except Exception as e:
        logger.error(f"Error procesando el archivo {csv_file}: {e}")
        return None