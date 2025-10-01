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
        if file_path.stat().st_size < 10:
            logger.warning(f"Omitiendo archivo de catálogo vacío: {file_path.name}")
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                catalogs_by_file[file_path.name] = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decodificando {file_path.name}")
                continue
    
    logger.info(f"Se cargaron {len(catalogs_by_file)} archivos de catálogo.")

    # 2. Iterar sobre cada estación en cada catálogo
    total_stations = 0
    updated_stations = 0
    for filename, stations in catalogs_by_file.items():
        if not isinstance(stations, list):
            continue
        total_stations += len(stations)
        for station in stations:
            station_id = station.get("ESTACION")
            if not station_id:
                continue

            # 3. Encontrar y leer el CSV correspondiente (con patrón corregido)
            pattern = f"dia*{station_id}.csv"
            csv_files = list(CSV_DIR.rglob(pattern))

            if not csv_files:
                logger.warning(f"No se encontró CSV para la estación {station_id} (Patrón: {pattern})")
                station["fecha_inicial_datos"] = None
                station["fecha_final_datos"] = None
                station["variables"] = []
                station["anios_de_datos"] = 0
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
                    station["anios_de_datos"] = 0
                    continue
                
                # 4. Extraer la información
                station["fecha_inicial_datos"] = date_col_df["Fecha"].iloc[0]
                station["fecha_final_datos"] = date_col_df["Fecha"].iloc[-1]
                station["variables"] = variables
                
                # 5. Calcular y añadir los años de datos
                try:
                    start_date = pd.to_datetime(station["fecha_inicial_datos"], format='%d/%m/%Y')
                    end_date = pd.to_datetime(station["fecha_final_datos"], format='%d/%m/%Y')
                    anios_de_datos = round((end_date - start_date).days / 365.25, 1)
                    station["anios_de_datos"] = anios_de_datos
                except (TypeError, ValueError):
                    station["anios_de_datos"] = 0

                updated_stations += 1
                # logger.info(f"Estación actualizada: {station_id}") # Opcional: descomentar para verbosidad

            except Exception as e:
                logger.error(f"Error procesando CSV para estación {station_id}: {e}")
                station["fecha_inicial_datos"] = None
                station["fecha_final_datos"] = None
                station["variables"] = []
                station["anios_de_datos"] = 0

    logger.info(f"Se procesaron {total_stations} estaciones, {updated_stations} actualizadas con datos.")

    # 6. Guardar los catálogos actualizados
    for filename, stations in catalogs_by_file.items():
        if not isinstance(stations, list):
            continue
        output_path = JSON_DIR / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stations, f, indent=2, ensure_ascii=False)
        logger.info(f"Catálogo actualizado y guardado en: {output_path}")

    logger.info("Proceso de enriquecimiento completado.")

if __name__ == "__main__":
    enrich_catalogs()