  Documentación Técnica del Proyecto Clicom2

  1. Resumen del Proyecto

  Este proyecto es un visor de datos de estaciones climatológicas. Permite a los usuarios explorar estaciones en un mapa interactivo, filtrar
  por estado y visualizar datos históricos a través de diferentes modos de agregación (diario, mensual, anual, etc.).

  La aplicación está dividida en dos componentes principales: un backend en Python que sirve los datos y un frontend en React que los
  visualiza.

  2. Tecnologías Utilizadas

  Backend:
   * Lenguaje: Python 3.11
   * Framework API: FastAPI
   * Servidor ASGI: Uvicorn
   * Análisis de Datos: Pandas, NumPy
   * Contenerización: Docker, Docker Compose

  Frontend:
   * Framework: React 19 con Vite
   * Lenguaje: JavaScript (JSX)
   * Librerías de UI: Ant Design, Ant Design Icons
   * Mapas: Leaflet
   * Gráficas: ECharts for React
   * Manejo de Fechas: Day.js

  3. Estructura del Proyecto

  El repositorio está organizado en dos carpetas principales:

   * frontend/: Contiene todo el código fuente de la aplicación de React.
   * backend/: Contiene el servidor de API de FastAPI y la lógica de procesamiento de datos.

    1 clicom2/
    2 ├── backend/
    3 │   ├── app/
    4 │   │   ├── data/             # Archivos de datos (CSV, JSON)
    5 │   │   ├── data_loader.py    # Lógica para cargar y procesar datos
    6 │   │   ├── estaciones.py     # Define los endpoints de la API
    7 │   │   ├── main.py           # Punto de entrada de la app FastAPI
    8 │   │   └── store.py          # Caché simple en memoria
    9 │   ├── Dockerfile            # "Plano" para construir la imagen Docker del backend
   10 │   └── docker-compose.yml    # Configuración para levantar el entorno de desarrollo
   11 └── frontend/
   12     ├── dist/                 # Carpeta con los archivos de producción (se genera)
   13     ├── src/
   14     │   ├── App.jsx           # Componente principal, maneja el estado global
   15     │   ├── SideDock.jsx      # Panel lateral de filtros
   16     │   └── BottomDock.jsx    # Panel inferior con la gráfica
   17     ├── package.json          # Dependencias y scripts del frontend
   18     └── vite.config.js        # Configuración de Vite

  4. Backend en Detalle

  El backend es una API de FastAPI que expone los datos climatológicos.

  Archivos Clave

   * `main.py`: Es el punto de entrada. Crea la aplicación FastAPI, configura CORS y, en modo producción, monta el directorio de archivos
     estáticos del frontend.
   * `estaciones.py`: Define todas las rutas (endpoints) de la API. Cada ruta corresponde a una forma de solicitar los datos.
   * `data_loader.py`: Es el corazón de la lógica de datos. Contiene funciones para:
       * Cargar y cachear los catálogos de estaciones y estados.
       * Calcular variables derivadas (TProm, TRango).
       * Calcular las diferentes agregaciones (promedio mensual, anual, ciclo anual, etc.).
   * `store.py`: Un módulo simple que actúa como una caché en memoria para evitar leer los archivos del disco en cada petición.

  Endpoints de la API

  Todos los endpoints se sirven bajo la ruta /estaciones/.

   * GET /estados: Devuelve el catálogo de estados.
   * GET /estaciones: Devuelve la lista completa de estaciones (con datos enriquecidos como rango de fechas y variables).
   * GET /estaciones/{estado}/{id}/datos: Devuelve los datos diarios de una estación.
   * GET /estaciones/{estado}/{id}/ciclo-anual: Devuelve el ciclo anual promediando los datos diarios.
   * GET /estaciones/{estado}/{id}/promedio-mensual: Devuelve el promedio de cada mes a lo largo de los años.
   * GET /estaciones/{estado}/{id}/promedio-anual: Devuelve el promedio de cada año.
   * GET /estaciones/{estado}/{id}/ciclo-anual-mensual: Devuelve el ciclo anual promediando los datos mensuales (12 puntos de dato).

  Todos los endpoints que devuelven series de tiempo aceptan los parámetros de consulta ?fecha_inicio=YYYY-MM-DD y ?fecha_fin=YYYY-MM-DD para
  filtrar los datos.

  5. Frontend en Detalle

  El frontend es una Single-Page Application (SPA) construida con React y Vite.

  Componentes Clave

   * `App.jsx`: Es el componente padre que orquesta toda la aplicación.
       * Maneja la mayoría del estado global: estación seleccionada, modo de gráfica, rango de fechas, etc.
       * Contiene la lógica para hacer las peticiones a la API del backend cada vez que un filtro o modo cambia.
       * Inicializa el mapa de Leaflet.
   * `SideDock.jsx`: Es el panel lateral. Es un componente "controlado" que recibe su estado (colapsado/expandido) y sus datos desde App.jsx.
     Contiene los filtros por estado y nombre.
   * `BottomDock.jsx`: Es el panel inferior que muestra la gráfica.
       * Recibe todos los datos necesarios como props desde App.jsx.
       * Usa la librería ECharts para renderizar la gráfica.
       * Contiene la lógica para cambiar entre los diferentes tipos de gráfica (Diarios, Ciclo Anual, etc.) y los selectores de fecha.

  6. Cómo Ejecutar el Proyecto

  Entorno de Desarrollo

   1. Backend: Desde la carpeta backend/, ejecuta docker compose up. El servidor de la API se levantará en http://localhost:8000 con recarga
      automática.
   2. Frontend: Desde la carpeta frontend/, ejecuta npm install (solo la primera vez) y luego npm run dev. El servidor de desarrollo del
      frontend se levantará en http://localhost:5173 y se conectará a la API en el puerto 8000.

  Entorno de Producción Local (Monolítico)

  Este modo empaqueta todo en un solo servidor, accesible en la red local.

   1. Construir el Frontend: Desde la carpeta frontend/, ejecuta npm run build. Esto crea la carpeta frontend/dist.
   2. Construir y Lanzar Docker: Desde la carpeta raíz del proyecto (clicom2/), ejecuta:

   1     docker compose -f docker-compose.prod.yml up --build -d
   3. Acceder: La aplicación estará disponible en http://localhost (o http://<tu-ip-local> para otros en la red).

  ---
