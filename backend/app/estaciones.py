from fastapi import APIRouter, HTTPException
from app import store
from app.data_loader import load_station_catalog, load_states_catalog, load_station_data

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
def datos_estacion_estado(estado: str, id: str):
    """
    Devuelve los datos climatológicos para una estación específica por su ID.
    Si los datos no están en caché, se cargan bajo demanda.
    
    - **estado**: Abreviatura del estado (actualmente no se usa en la lógica, pero se mantiene en la ruta por compatibilidad).
    - **id**: ID único de la estación.
    """
    datos = store.STATION_DATA.get(id)
    if datos is None:
        datos = load_station_data(id)
        if datos is None:
            raise HTTPException(status_code=404, detail=f"Datos no encontrados para la estación con ID {id}")
    return datos

@router.get("/estados", summary="Obtener el catálogo de estados de México")
def obtener_estados():
    """
    Devuelve una lista de todos los estados de México con sus abreviaturas.
    Si el catálogo no está en caché, se carga bajo demanda.
    """
    if not store.STATES_CATALOG:
        load_states_catalog()
    return store.STATES_CATALOG