import pandas as pd
import json
from pathlib import Path
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
APP_DIR = Path(__file__).parent / "app"
JSON_DIR = APP_DIR / "data" / "json"
CSV_DIR = APP_DIR / "data" / "csv"

def enrich_catalogs():
    logger.info("Iniciando el proceso de enriquecimiento de catálogos...")

    # 1. Cargar todos los catálogos de estaciones en un diccionario por nombre de archivo
    catalogs_by_file = {}
    json_files = list(JSON_DIR.glob("*_catalogo_estaciones_climatologicas.json"))
    if not json_files:
        logger.error("No se encontraron archivos de catálogo JSON.")
        return

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            catalogs_by_file[file_path.name] = json.load(f)
    
    logger.info(f"Se cargaron {len(catalogs_by_file)} archivos de catálogo.")

    # 2. Iterar sobre cada estación en cada catálogo
    total_stations = 0
    updated_stations = 0
    for filename, stations in catalogs_by_file.items():
        total_stations += len(stations)
        for station in stations:
            station_id = station.get("ESTACION")
            if not station_id:
                continue

            # 3. Encontrar y leer el CSV correspondiente
            pattern = f"dia{station_id}.csv" if not str(station_id).isnumeric() else f"dia0{station_id}.csv"
            csv_files = list(CSV_DIR.rglob(pattern))

            if not csv_files:
                logger.warning(f"No se encontró CSV para la estación {station_id} (Patrón: {pattern})")
                station["fecha_inicial_datos"] = None
                station["fecha_final_datos"] = None
                station["variables"] = []
                continue

            try:
                # Leer solo la columna de fecha para obtener el rango de manera eficiente
                date_col_df = pd.read_csv(csv_files[0], usecols=['Fecha'], encoding="utf-8", low_memory=True).dropna(how="all")
                
                # Leer solo la primera fila para obtener las columnas de variables
                header_df = pd.read_csv(csv_files[0], nrows=0, encoding="utf-8")
                variables = [col for col in header_df.columns if col != 'Fecha']

                if "Fecha" not in date_col_df.columns or date_col_df.empty:
                    station["fecha_inicial_datos"] = None
                    station["fecha_final_datos"] = None
                    station["variables"] = variables
                    continue
                
                # 4. Extraer la información
                station["fecha_inicial_datos"] = date_col_df["Fecha"].iloc[0]
                station["fecha_final_datos"] = date_col_df["Fecha"].iloc[-1]
                station["variables"] = variables
                updated_stations += 1
                logger.info(f"Estación actualizada: {station_id}")

            except Exception as e:
                logger.error(f"Error procesando CSV para estación {station_id}: {e}")
                station["fecha_inicial_datos"] = None
                station["fecha_final_datos"] = None
                station["variables"] = []

    logger.info(f"Se procesaron {total_stations} estaciones, {updated_stations} actualizadas con datos.")

    # 5. Guardar los catálogos actualizados
    for filename, stations in catalogs_by_file.items():
        output_path = JSON_DIR / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stations, f, indent=2, ensure_ascii=False)
        logger.info(f"Catálogo actualizado y guardado en: {output_path}")

    logger.info("Proceso de enriquecimiento completado.")

if __name__ == "__main__":
    enrich_catalogs()