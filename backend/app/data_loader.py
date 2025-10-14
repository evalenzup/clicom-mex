"""
Módulo para cargar y procesar todos los datos al inicio de la aplicación.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging
from scipy.stats import linregress
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

    # Extraer la parte numérica del ID, que es lo que está en el nombre del archivo.
    try:
        numeric_id = station_id.split('/')[-1]
    except:
        numeric_id = station_id

    # Construir un patrón para encontrar el archivo en cualquier subdirectorio,
    # buscando por la terminación numérica.
    pattern = f"dia*{numeric_id}.csv"

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

        # Convertir la fecha UNA SOLA VEZ al cargar los datos.
        # Esto optimiza todos los cálculos posteriores.
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        df.dropna(subset=['Fecha'], inplace=True) # Eliminar filas donde la fecha no fue válida
        df = df.sort_values(by='Fecha').reset_index(drop=True)

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
            # Formatear a string para el JSON de metadatos
            "inicio": df["Fecha"].iloc[0].strftime('%d/%m/%Y') if not df.empty else None,
            "fin": df["Fecha"].iloc[-1].strftime('%d/%m/%Y') if not df.empty else None,
        }

        station_data = {
            "variables": variables,
            "periodo": periodo,
            # Guardamos el DataFrame con fechas como datetime para eficiencia
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

def filter_data_by_date(df: pd.DataFrame, start_date: str | None, end_date: str | None) -> pd.DataFrame:
    """Función de utilidad para filtrar un DataFrame por rango de fechas."""
    if df.empty:
        return df
    # La columna 'Fecha' ya es de tipo datetime
    if start_date:
        df = df[df['Fecha'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Fecha'] <= pd.to_datetime(end_date)]
    return df

def get_aggregation_map(columns: list) -> dict:
    """
    Crea un diccionario de agregación para Pandas.
    Suma las variables de precipitación/evaporación y promedia el resto.
    """
    # Variables que deben ser sumadas en lugar de promediadas
    SUM_VARS = ["PRECIP", "EVAP"] 
    
    agg_map = {}
    for col in columns:
        if col in SUM_VARS:
            agg_map[col] = 'sum'
        else:
            agg_map[col] = 'mean'
    return agg_map

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
    
    # La columna 'Fecha' ya es datetime. Convertimos los datos de 'records' a DataFrame.
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    df['month'] = df['Fecha'].dt.month
    df['day'] = df['Fecha'].dt.day

    # Agrupar por día y mes, aplicando la agregación correcta a cada variable
    agg_map = get_aggregation_map(numeric_cols)
    # FIX: Para el ciclo anual diario, necesitamos promediar todas las variables,
    # incluyendo PRECIP y EVAP, para obtener el valor promedio de cada día del año.
    # El mapa de agregación por defecto suma estas variables, lo cual es incorrecto aquí.
    if 'PRECIP' in agg_map:
        agg_map['PRECIP'] = 'mean'
    if 'EVAP' in agg_map:
        agg_map['EVAP'] = 'mean'
    cycle_df = df.groupby(['month', 'day']).agg(agg_map).reset_index()

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

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Agrupar por mes y aplicar la agregación correcta
    agg_map = get_aggregation_map(numeric_cols)
    monthly_df = df.groupby(df['Fecha'].dt.to_period('M')).agg(agg_map).reset_index()
    
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

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Agrupar por año y aplicar la agregación correcta
    agg_map = get_aggregation_map(numeric_cols)
    yearly_df = df.groupby(df['Fecha'].dt.to_period('Y')).agg(agg_map).reset_index()
    
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

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    df['Month'] = df['Fecha'].dt.month
    df['Year'] = df['Fecha'].dt.year

    # Definir columnas para suma y promedio
    sum_cols = [col for col in numeric_cols if col in ["PRECIP", "EVAP"]]
    mean_cols = [col for col in numeric_cols if col not in sum_cols]

    # Crear mapa de agregación para el primer paso (agregados por mes dentro de cada año)
    agg_map_yearly = {col: 'sum' for col in sum_cols}
    agg_map_yearly.update({col: 'mean' for col in mean_cols})

    # Paso 1: Calcular agregados mensuales para cada año
    yearly_monthly_df = df.groupby(['Year', 'Month']).agg(agg_map_yearly).reset_index()

    # Paso 2: Calcular el promedio de esos agregados a través de todos los años
    final_df = yearly_monthly_df.groupby('Month')[numeric_cols].mean().reset_index()
    
    # Renombrar la columna 'Month' a 'Mes' para claridad y consistencia
    final_df = final_df.rename(columns={'Month': 'Mes'})
    final_df = final_df.sort_values(by='Mes')
    
    final_df = final_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": final_df.to_dict(orient="records")
    }

def calculate_seasonal_average(station_id: str, start_date: str | None = None, end_date: str | None = None):
    """Calcula el agregado (promedio/suma) para cada estación de cada año."""
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando agregados estacionales por año para la estación {station_id}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty:
        return {"variables": station_full_data['variables'], "datos": []}

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Mapeo de meses a estaciones del año (hemisferio norte)
    seasons = {
        12: 'Invierno', 1: 'Invierno', 2: 'Invierno',
        3: 'Primavera', 4: 'Primavera', 5: 'Primavera',
        6: 'Verano', 7: 'Verano', 8: 'Verano',
        9: 'Otoño', 10: 'Otoño', 11: 'Otoño'
    }
    df['Season'] = df['Fecha'].dt.month.map(seasons)
    df['Year'] = df['Fecha'].dt.year

    # Agrupar por año y luego por estación, y aplicar la agregación
    agg_map = get_aggregation_map(numeric_cols)
    seasonal_df = df.groupby(['Year', 'Season']).agg(agg_map).reset_index()

    # Crear una columna de etiqueta para el eje X
    seasonal_df['Fecha'] = seasonal_df['Season'] + ' ' + seasonal_df['Year'].astype(str)

    # Asegurar el orden cronológico correcto
    season_order = ['Primavera', 'Verano', 'Otoño', 'Invierno']
    seasonal_df['Season'] = pd.Categorical(seasonal_df['Season'], categories=season_order, ordered=True)
    seasonal_df = seasonal_df.sort_values(['Year', 'Season'])

    seasonal_df = seasonal_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": seasonal_df.to_dict(orient="records")
    }

def calculate_seasonal_cycle(station_id: str, start_date: str | None = None, end_date: str | None = None):
    """
    Calcula el ciclo anual estacional.
    Para PRECIP/EVAP: es el promedio de los acumulados estacionales de cada año.
    Para el resto: es el promedio de los promedios estacionales de cada año.
    """
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando ciclo anual estacional para la estación {station_id}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty:
        return {"variables": station_full_data['variables'], "datos": []}

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": numeric_cols, "datos": []}

    # Mapeo de meses a estaciones
    seasons = {
        12: 'Invierno', 1: 'Invierno', 2: 'Invierno',
        3: 'Primavera', 4: 'Primavera', 5: 'Primavera',
        6: 'Verano', 7: 'Verano', 8: 'Verano',
        9: 'Otoño', 10: 'Otoño', 11: 'Otoño'
    }
    df['Season'] = df['Fecha'].dt.month.map(seasons)
    df['Year'] = df['Fecha'].dt.year

    # Definir columnas para suma y promedio
    sum_cols = [col for col in numeric_cols if col in ["PRECIP", "EVAP"]]
    mean_cols = [col for col in numeric_cols if col not in sum_cols]

    # Crear mapa de agregación para el primer paso (agregados por estación dentro de cada año)
    agg_map_yearly = {col: 'sum' for col in sum_cols}
    agg_map_yearly.update({col: 'mean' for col in mean_cols})

    # Paso 1: Calcular agregados estacionales para cada año
    yearly_seasonal_df = df.groupby(['Year', 'Season']).agg(agg_map_yearly).reset_index()

    # Paso 2: Calcular el promedio de esos agregados a través de todos los años
    final_df = yearly_seasonal_df.groupby('Season')[numeric_cols].mean().reset_index()

    # Asegurar el orden correcto de las estaciones
    season_order = ['Primavera', 'Verano', 'Otoño', 'Invierno']
    final_df['Season'] = pd.Categorical(final_df['Season'], categories=season_order, ordered=True)
    final_df = final_df.round(2).replace({np.nan: None})

    return {
        "variables": numeric_cols,
        "datos": final_df.to_dict(orient="records")
    }

def calculate_daily_percentiles(station_id: str, variable: str, percentile: int, start_date: str | None = None, end_date: str | None = None):
    """
    Calcula los percentiles diarios para una variable y estación dadas.
    """
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        station_full_data = load_station_data(station_id)
        if not station_full_data:
            return None

    logger.info(f"Calculando percentiles diarios para la estación {station_id}, variable {variable}, percentil {percentile}...")
    df = pd.DataFrame(station_full_data['datos'])
    if df.empty or variable not in df.columns:
        return {"variables": [], "datos": []}

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = filter_data_by_date(df, start_date, end_date)
    if df.empty:
        return {"variables": [], "datos": []}

    # Asegurarse de que la variable es numérica
    df[variable] = pd.to_numeric(df[variable], errors='coerce')
    df = df.dropna(subset=[variable])

    df['month'] = df['Fecha'].dt.month
    df['day'] = df['Fecha'].dt.day

    # Calcular el percentil
    q = percentile / 100.0
    percentile_df = df.groupby(['month', 'day'])[variable].quantile(q).reset_index()
    percentile_df = percentile_df.rename(columns={variable: f"p{percentile}"})

    percentile_df['dia_mes'] = percentile_df.apply(lambda row: f"{int(row['day']):02d}-{int(row['month']):02d}", axis=1)
    
    percentile_df = percentile_df.round(2).replace({np.nan: None})

    return {
        "variables": [f"p{percentile}"],
        "datos": percentile_df.to_dict(orient="records")
    }

def calculate_extreme_event_frequency(station_id: str, variable: str, percentile: int, operator: str, start_date: str | None = None, end_date: str | None = None):
    """
    Calcula la frecuencia anual de eventos extremos para una variable y percentil dados.
    """
    # 1. Obtener los umbrales de percentiles diarios
    percentiles_data = calculate_daily_percentiles(station_id, variable, percentile, start_date, end_date)
    if not percentiles_data or not percentiles_data.get('datos'):
        return {"variables": [], "datos": []}
    
    percentile_df = pd.DataFrame(percentiles_data['datos'])
    # Renombrar la columna del percentil para la fusión
    percentile_df = percentile_df.rename(columns={f"p{percentile}": 'threshold'})

    # 2. Obtener los datos brutos de la estación
    station_full_data = store.STATION_DATA.get(station_id)
    if not station_full_data:
        # No debería pasar si calculate_daily_percentiles funcionó, pero por si acaso
        return {"variables": [], "datos": []}

    df = pd.DataFrame(station_full_data['datos'])
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = filter_data_by_date(df, start_date, end_date)
    if df.empty or variable not in df.columns:
        return {"variables": [], "datos": []}

    df[variable] = pd.to_numeric(df[variable], errors='coerce')
    df = df.dropna(subset=[variable])

    # 3. Preparar para la fusión
    df['month'] = df['Fecha'].dt.month
    df['day'] = df['Fecha'].dt.day

    # 4. Fusionar datos diarios con umbrales
    merged_df = pd.merge(df, percentile_df[['month', 'day', 'threshold']], on=['month', 'day'])

    # 5. Identificar eventos extremos
    if operator == 'greater':
        merged_df['is_extreme'] = merged_df[variable] > merged_df['threshold']
    elif operator == 'less':
        merged_df['is_extreme'] = merged_df[variable] < merged_df['threshold']
    else:
        raise ValueError("El operador debe ser 'greater' o 'less'")

    # 6. Contar eventos por año
    merged_df['year'] = merged_df['Fecha'].dt.year
    frequency_df = merged_df.groupby('year')['is_extreme'].sum().reset_index()
    frequency_df = frequency_df.rename(columns={'is_extreme': 'frequency', 'year': 'Fecha'})

    frequency_df = frequency_df.round(2).replace({np.nan: None})

    # 7. Calcular la línea de tendencia
    trend_data = {}
    if not frequency_df.empty and len(frequency_df) > 1:
        x = frequency_df['Fecha']
        y = frequency_df['frequency']
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        
        # Crear los puntos de la línea de tendencia
        trend_line = (slope * x + intercept).tolist()
        
        trend_data = {
            "slope": slope,
            "p_value": p_value,
            "is_significant": bool(p_value < 0.05),
            "trend_line_points": trend_line
        }

    return {
        "variables": ['frequency'],
        "datos": frequency_df.to_dict(orient="records"),
        "trend": trend_data
    }