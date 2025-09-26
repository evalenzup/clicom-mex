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
    """
    Carga el catálogo de estaciones desde los archivos JSON, asegurando que no haya duplicados.
    """
    logger.info("Cargando catálogo de estaciones...")
    station_dict = {}
    for json_file in JSON_DIR.glob("*_catalogo_estaciones_climatologicas.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            stations = json.load(f)
            for station in stations:
                # Usar una clave única para evitar duplicados
                key = f"{station.get('ESTADO')}-{station.get('ESTACION')}"
                station_dict[key] = station
    
    catalogs = list(station_dict.values())
    store.STATION_CATALOG = catalogs
    logger.info(f"Catálogo de estaciones cargado con {len(catalogs)} registros únicos.")

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

        # Calcular TProm si TMAX y TMIN están presentes
        if 'TMAX' in df.columns and 'TMIN' in df.columns:
            # Asegurarse de que las columnas son numéricas para la operación
            df['TMAX'] = pd.to_numeric(df['TMAX'], errors='coerce')
            df['TMIN'] = pd.to_numeric(df['TMIN'], errors='coerce')
            df['TProm'] = ((df['TMAX'] + df['TMIN']) / 2).round(2)
            df['TRango'] = (df['TMAX'] - df['TMIN']).round(2)
        
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
        logger.info(f"Variables disponibles: {station_data['variables']}")
        logger.info(f"Período de datos: {station_data['periodo']['inicio']} a {station_data['periodo']['fin']}")
        return station_data

    except Exception as e:
        logger.error(f"Error procesando el archivo {csv_file}: {e}")
        return None

def calculate_annual_cycle(station_id: str, start_date: str | None = None, end_date: str | None = None):
    """Calcula el ciclo anual para una estación dada, opcionalmente filtrando por un rango de fechas."""
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando ciclo anual para la estación {station_id}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty:
        return {"variables": station_full_data['variables'], "datos": []}

    # Identify numeric columns BEFORE adding month/day
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')

    # Filtrar por rango de fechas si se proporciona
    if start_date:
        df = df[df['Fecha'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Fecha'] <= pd.to_datetime(end_date)]
    
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    df['month'] = df['Fecha'].dt.month
    df['day'] = df['Fecha'].dt.day

    # Now, groupby month and day, and aggregate only the original numeric columns
    cycle_df = df.groupby(['month', 'day'])[numeric_cols].mean().reset_index()

    cycle_df['dia_mes'] = cycle_df.apply(lambda row: f"{int(row['day']):02d}-{int(row['month']):02d}", axis=1)
    
    cycle_df = cycle_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": cycle_df.to_dict(orient="records")
    }

def calculate_monthly_average(station_id: str, start_date: str | None = None, end_date: str | None = None):
    """Calcula el promedio mensual para una estación dada, opcionalmente filtrando por un rango de fechas."""
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando promedio mensual para la estación {station_id}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty:
        return {"variables": station_full_data['variables'], "datos": []}

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')

    # Filtrar por rango de fechas si se proporciona
    if start_date:
        df = df[df['Fecha'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Fecha'] <= pd.to_datetime(end_date)]

    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Agrupar por mes y calcular la media
    monthly_df = df.groupby(df['Fecha'].dt.to_period('M'))[numeric_cols].mean().reset_index()
    
    # Convertir el periodo a string 'YYYY-MM'
    monthly_df['Fecha'] = monthly_df['Fecha'].dt.strftime('%Y-%m')
    
    monthly_df = monthly_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": monthly_df.to_dict(orient="records")
    }

def calculate_yearly_average(station_id: str, start_date: str | None = None, end_date: str | None = None):
    """Calcula el promedio anual para una estación dada, opcionalmente filtrando por un rango de fechas."""
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando promedio anual para la estación {station_id}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty:
        return {"variables": station_full_data['variables'], "datos": []}

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')

    # Filtrar por rango de fechas si se proporciona
    if start_date:
        df = df[df['Fecha'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Fecha'] <= pd.to_datetime(end_date)]

    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Agrupar por año y calcular la media
    yearly_df = df.groupby(df['Fecha'].dt.to_period('Y'))[numeric_cols].mean().reset_index()
    
    # Convertir el periodo a string 'YYYY'
    yearly_df['Fecha'] = yearly_df['Fecha'].dt.strftime('%Y')
    
    yearly_df = yearly_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": yearly_df.to_dict(orient="records")
    }

def calculate_monthly_annual_cycle(station_id: str, start_date: str | None = None, end_date: str | None = None):
    """Calcula el ciclo anual de promedios mensuales para una estación dada."""
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando ciclo anual mensual para la estación {station_id}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty:
        return {"variables": station_full_data['variables'], "datos": []}

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')

    # Filtrar por rango de fechas si se proporciona
    if start_date:
        df = df[df['Fecha'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Fecha'] <= pd.to_datetime(end_date)]

    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Agrupar por mes y calcular la media
    monthly_cycle_df = df.groupby(df['Fecha'].dt.month)[numeric_cols].mean().reset_index()
    
    # Renombrar la columna 'Fecha' a 'Mes' para claridad
    monthly_cycle_df = monthly_cycle_df.rename(columns={'Fecha': 'Mes'})
    monthly_cycle_df = monthly_cycle_df.sort_values(by='Mes')
    
    monthly_cycle_df = monthly_cycle_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": monthly_cycle_df.to_dict(orient="records")
    }