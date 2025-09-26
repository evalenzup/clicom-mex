from fastapi import APIRouter, HTTPException, Query
from app import store
from app.data_loader import load_station_catalog, load_states_catalog, load_station_data, calculate_annual_cycle, calculate_monthly_average, calculate_yearly_average, calculate_monthly_annual_cycle
import pandas as pd
import numpy as np

router = APIRouter()

@router.get("/estaciones", summary="Obtener el catálogo de todas las estaciones")
def listar_estaciones():
    """
    Devuelve una lista de todas las estaciones climatológicas del catálogo.
    Si el catálogo no está en caché, se carga bajo demanda.
    """
    if not store.STATION_CATALOG:
        load_station_catalog()
    return store.STATION_CATALOG

@router.get("/estaciones/{estado}/{id}/datos", summary="Obtener datos de una estación específica")
def datos_estacion_estado(
    estado: str, 
    id: str,
    start_date: str | None = Query(default=None, alias="fecha_inicio"),
    end_date: str | None = Query(default=None, alias="fecha_fin")
):
    """
    Devuelve los datos climatológicos para una estación específica por su ID.
    Si los datos no están en caché, se cargan bajo demanda.
    
    - **estado**: Abreviatura del estado (actualmente no se usa en la lógica, pero se mantiene en la ruta por compatibilidad).
    - **id**: ID único de la estación.
    - **fecha_inicio**: Fecha de inicio para filtrar los datos (formato YYYY-MM-DD).
    - **fecha_fin**: Fecha de fin para filtrar los datos (formato YYYY-MM-DD).
    """
    full_data = store.STATION_DATA.get(id)
    if full_data is None:
        full_data = load_station_data(id)
        if full_data is None:
            raise HTTPException(status_code=404, detail=f"Datos no encontrados para la estación con ID {id}")

    # Si no hay fechas de filtro, devolver todos los datos
    if not start_date and not end_date:
        return full_data

    # Si hay fechas, filtrar
    df = pd.DataFrame(full_data['datos'])
    if df.empty:
        return full_data # Devuelve la estructura vacía si no hay datos

    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')

    if start_date:
        df = df[df['Fecha'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Fecha'] <= pd.to_datetime(end_date)]

    # Devolver los datos filtrados con la misma estructura
    # Reemplazar NaNs por Nones para que sea compatible con JSON
    df = df.replace({np.nan: None})
    # Convertir la columna de fecha de nuevo a string para la respuesta JSON
    df['Fecha'] = df['Fecha'].dt.strftime('%d/%m/%Y')
    filtered_datos = df.to_dict(orient='records')
    
    # Actualizar el periodo en la respuesta
    periodo_filtrado = {
        "inicio": filtered_datos[0]['Fecha'] if filtered_datos else None,
        "fin": filtered_datos[-1]['Fecha'] if filtered_datos else None,
    }

    return {
        "variables": full_data['variables'],
        "periodo": periodo_filtrado,
        "datos": filtered_datos
    }

@router.get("/estaciones/{estado}/{id}/ciclo-anual", summary="Calcula el ciclo anual de una estación")
def obtener_ciclo_anual(
    id: str,
    start_date: str | None = Query(default=None, alias="fecha_inicio"),
    end_date: str | None = Query(default=None, alias="fecha_fin")
):
    """
    Calcula el promedio de cada día del año para todas las variables numéricas
    de una estación específica.
    """
    ciclo_data = calculate_annual_cycle(id, start_date=start_date, end_date=end_date)
    if ciclo_data is None:
        raise HTTPException(status_code=404, detail=f"Datos no encontrados para calcular el ciclo anual de la estación con ID {id}")
    return ciclo_data

@router.get("/estados", summary="Obtener el catálogo de estados de México")
def obtener_estados():
    """
    Devuelve una lista de todos los estados de México con sus abreviaturas.
    Si el catálogo no está en caché, se carga bajo demanda.
    """
    if not store.STATES_CATALOG:
        load_states_catalog()
    return store.STATES_CATALOG

@router.get("/estaciones/{estado}/{id}/promedio-mensual", summary="Calcula el promedio mensual de una estación")
def obtener_promedio_mensual(
    id: str,
    start_date: str | None = Query(default=None, alias="fecha_inicio"),
    end_date: str | None = Query(default=None, alias="fecha_fin")
):
    """
    Calcula el promedio de cada mes para todas las variables numéricas
    de una estación específica, opcionalmente dentro de un rango de fechas.
    """
    monthly_data = calculate_monthly_average(id, start_date=start_date, end_date=end_date)
    if monthly_data is None:
        raise HTTPException(status_code=404, detail=f"Datos no encontrados para calcular el promedio mensual de la estación con ID {id}")
    return monthly_data

@router.get("/estaciones/{estado}/{id}/promedio-anual", summary="Calcula el promedio anual de una estación")
def obtener_promedio_anual(
    id: str,
    start_date: str | None = Query(default=None, alias="fecha_inicio"),
    end_date: str | None = Query(default=None, alias="fecha_fin")
):
    """
    Calcula el promedio de cada año para todas las variables numéricas
    de una estación específica, opcionalmente dentro de un rango de fechas.
    """
    yearly_data = calculate_yearly_average(id, start_date=start_date, end_date=end_date)
    if yearly_data is None:
        raise HTTPException(status_code=404, detail=f"Datos no encontrados para calcular el promedio anual de la estación con ID {id}")
    return yearly_data

@router.get("/estaciones/{estado}/{id}/ciclo-anual-mensual", summary="Calcula el ciclo anual de promedios mensuales para una estación")
def obtener_ciclo_anual_mensual(
    id: str,
    start_date: str | None = Query(default=None, alias="fecha_inicio"),
    end_date: str | None = Query(default=None, alias="fecha_fin")
):
    """
    Calcula el promedio de cada mes a lo largo de todos los años para una estación.
    """
    data = calculate_monthly_annual_cycle(id, start_date=start_date, end_date=end_date)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Datos no encontrados para calcular el ciclo anual mensual de la estación con ID {id}")
    return data