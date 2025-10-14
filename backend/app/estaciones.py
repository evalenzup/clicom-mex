from fastapi import APIRouter, HTTPException, Query, Depends
from . import store
from .data_loader import (
    load_station_catalog, 
    load_states_catalog, 
    load_station_data, 
    calculate_annual_cycle, 
    calculate_monthly_average, 
    calculate_yearly_average, 
    calculate_monthly_annual_cycle,
    calculate_seasonal_average,
    calculate_seasonal_cycle,
    calculate_daily_percentiles,
    calculate_extreme_event_frequency,
    filter_data_by_date
)
import pandas as pd
import numpy as np

router = APIRouter(
    tags=["estaciones"]
)

@router.get("/estaciones", summary="Obtener el catálogo de todas las estaciones")
def listar_estaciones():
    """
    Devuelve una lista de todas las estaciones climatológicas del catálogo.
    Si el catálogo no está en caché, se carga bajo demanda.
    """
    if not store.STATION_CATALOG:
        load_station_catalog()
    return store.STATION_CATALOG

def get_station_data(id: str) -> pd.DataFrame:
    """
    Dependencia de FastAPI para obtener los datos de una estación como DataFrame.
    Carga los datos si no están en caché y maneja el error 404.
    """
    full_data = store.STATION_DATA.get(id)
    if full_data is None:
        full_data = load_station_data(id)
        if full_data is None:
            raise HTTPException(status_code=404, detail=f"Datos no encontrados para la estación con ID {id}")
    
    # Devolvemos el DataFrame directamente para su procesamiento
    return full_data

class DateFilters:
    """Dependencia para agrupar los parámetros de filtro de fecha."""
    def __init__(
        self,
        start_date: str | None = Query(default=None, alias="fecha_inicio", description="Fecha de inicio (YYYY-MM-DD)"),
        end_date: str | None = Query(default=None, alias="fecha_fin", description="Fecha de fin (YYYY-MM-DD)"),
    ):
        self.start_date = start_date
        self.end_date = end_date

@router.get("/estaciones/{id:path}/datos", summary="Obtener datos de una estación específica")
def datos_estacion_estado(
    id: str, 
    full_data: dict = Depends(get_station_data),
    date_filters: DateFilters = Depends()
):
    """
    Devuelve los datos climatológicos para una estación específica por su ID.
    - **id**: ID único de la estación.
    - **fecha_inicio**: Fecha de inicio para filtrar los datos (formato YYYY-MM-DD).
    - **fecha_fin**: Fecha de fin para filtrar los datos (formato YYYY-MM-DD).
    """
    df = pd.DataFrame(full_data['datos'])
    
    # La columna 'Fecha' ya es datetime gracias a la optimización en data_loader
    filtered_df = filter_data_by_date(df, date_filters.start_date, date_filters.end_date)

    filtered_df = filtered_df.replace({np.nan: None})
    filtered_df['Fecha'] = filtered_df['Fecha'].dt.strftime('%d/%m/%Y')
    filtered_datos = filtered_df.to_dict(orient='records')
    
    periodo_filtrado = {
        "inicio": filtered_datos[0]['Fecha'] if filtered_datos else None,
        "fin": filtered_datos[-1]['Fecha'] if filtered_datos else None,
    }

    return {
        "variables": full_data['variables'], # Las variables no cambian con el filtro
        "periodo": periodo_filtrado,
        "datos": filtered_datos
    }

@router.get("/estaciones/{id:path}/ciclo-anual", summary="Calcula el ciclo anual de una estación")
def obtener_ciclo_anual(
    id: str,
    date_filters: DateFilters = Depends()
):
    """
    Calcula el promedio de cada día del año para todas las variables numéricas
    de una estación específica.
    """
    return calculate_annual_cycle(id, start_date=date_filters.start_date, end_date=date_filters.end_date)

@router.get("/estados", summary="Obtener el catálogo de estados de México")
def obtener_estados():
    """
    Devuelve una lista de todos los estados de México con sus abreviaturas.
    Si el catálogo no está en caché, se carga bajo demanda.
    """
    if not store.STATES_CATALOG:
        load_states_catalog()
    return store.STATES_CATALOG

@router.get("/estaciones/{id:path}/promedio-mensual", summary="Calcula el promedio mensual de una estación")
def obtener_promedio_mensual(
    id: str,
    date_filters: DateFilters = Depends()
):
    """
    Calcula el promedio de cada mes para todas las variables numéricas
    de una estación específica, opcionalmente dentro de un rango de fechas.
    """
    return calculate_monthly_average(id, start_date=date_filters.start_date, end_date=date_filters.end_date)

@router.get("/estaciones/{id:path}/promedio-anual", summary="Calcula el promedio anual de una estación")
def obtener_promedio_anual(
    id: str,
    date_filters: DateFilters = Depends()
):
    """
    Calcula el promedio de cada año para todas las variables numéricas
    de una estación específica, opcionalmente dentro de un rango de fechas.
    """
    return calculate_yearly_average(id, start_date=date_filters.start_date, end_date=date_filters.end_date)

@router.get("/estaciones/{id:path}/ciclo-anual-mensual", summary="Calcula el ciclo anual de promedios mensuales para una estación")
def obtener_ciclo_anual_mensual(
    id: str,
    date_filters: DateFilters = Depends()
):
    """
    Calcula el promedio de cada mes a lo largo de todos los años para una estación.
    """
    return calculate_monthly_annual_cycle(id, start_date=date_filters.start_date, end_date=date_filters.end_date)

@router.get("/estaciones/{id:path}/estacional", summary="Calcula el agregado estacional de una estación")
def obtener_agregado_estacional(
    id: str,
    date_filters: DateFilters = Depends()
):
    """
    Calcula el agregado (promedio o suma) para cada estación del año (invierno, primavera, etc.)
    para todas las variables numéricas de una estación específica.
    """
    return calculate_seasonal_average(id, start_date=date_filters.start_date, end_date=date_filters.end_date)

@router.get("/estaciones/{id:path}/ciclo-anual-estacional", summary="Calcula el ciclo anual estacional de una estación")
def obtener_ciclo_anual_estacional(
    id: str,
    date_filters: DateFilters = Depends()
):
    """
    Calcula el promedio de los agregados estacionales para cada año.
    """
    return calculate_seasonal_cycle(id, start_date=date_filters.start_date, end_date=date_filters.end_date)

@router.get("/estaciones/{id:path}/percentiles-diarios", summary="Calcula los percentiles diarios para una variable")
def obtener_percentiles_diarios(
    id: str,
    variable: str = Query(..., description="La variable a calcular (ej. TMAX, TMIN, PRECIP)"),
    percentil: int = Query(..., ge=0, le=100, description="El percentil a calcular (0-100)"),
    date_filters: DateFilters = Depends()
):
    """
    Calcula un percentil específico para cada día del año para una variable dada.
    """
    return calculate_daily_percentiles(
        id, 
        variable=variable, 
        percentile=percentil, 
        start_date=date_filters.start_date, 
        end_date=date_filters.end_date
    )

@router.get("/estaciones/{id:path}/extremos/frecuencia", summary="Calcula la frecuencia de eventos extremos")
def obtener_frecuencia_eventos_extremos(
    id: str,
    variable: str = Query(..., description="La variable a analizar (ej. TMAX, TMIN, PRECIP)"),
    percentil: int = Query(..., ge=0, le=100, description="El percentil para el umbral (0-100)"),
    operator: str = Query(..., description="El operador de comparación ('greater' o 'less')"),
    date_filters: DateFilters = Depends()
):
    """
    Calcula la frecuencia anual de días que superan un umbral de percentil.
    """
    if operator not in ['greater', 'less']:
        raise HTTPException(status_code=400, detail="El operador debe ser 'greater' o 'less'")
    
    return calculate_extreme_event_frequency(
        id,
        variable=variable,
        percentile=percentil,
        operator=operator,
        start_date=date_filters.start_date,
        end_date=date_filters.end_date
    )