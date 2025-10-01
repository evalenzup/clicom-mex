import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Arreglo para los íconos de Leaflet en producción con Vite
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});


import SideDock from './SideDock';
import BottomDock from './BottomDock';
import './App.css';

import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
dayjs.extend(customParseFormat);


const API_BASE = '/api';

/* ===== Utils ===== */
const cleanNumber = (val) => {
  if (val == null) return NaN;
  const s = String(val).replace(/[^\d\-\.\,]/g, '').replace(',', '.').trim();
  return parseFloat(s);
};

/* ===== Basemaps (fábricas) ===== */
const basemaps = {
  OSM: () =>
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
  Satelite: () =>
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 20 }),
  CartoLight: () =>
    L.tileLayer('https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }),
  Topo: () =>
    L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17 })
};

export default function App() {
  // filtros / catálogos
  const [estados, setEstados] = useState([]); // [{value,label}]
  const [estadosMap, setEstadosMap] = useState({});
  const [selectedEstado, setSelectedEstado] = useState(null);
  const [query, setQuery] = useState('');

  const [minAnios, setMinAnios] = useState(0);
  const [filterDateRange, setFilterDateRange] = useState([null, null]);

  // estaciones
  const [allStations, setAllStations] = useState([]);
  const [filteredStations, setFilteredStations] = useState([]);

  // mapa
  const [activeBasemap, setActiveBasemap] = useState('OSM');
  const [fitAll, setFitAll] = useState(true);
  const [sideDockCollapsed, setSideDockCollapsed] = useState(false);


  // sidedock
  const [sideOpen, setSideOpen] = useState(true);

  // estación/series
  const [selectedStation, setSelectedStation] = useState(null);
  const [chartData, setChartData] = useState(null); // {variables:[], datos:[{Fecha,...}]}
  const [loadingChart, setLoadingChart] = useState(false);
  const [selectedVars, setSelectedVars] = useState([]); // variables visibles
  const [dateRange, setDateRange] = useState([null, null]);

  // refs de mapa
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const baseLayer = useRef(null);
  const markersLayer = useRef(null);
  const markersIndex = useRef({}); // <-- índice { "ESTADO-ESTACION": marker }

  const serieAbortRef = useRef(null);

  /* == cargar estados == */
  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/estados`, { signal: ac.signal });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        const options = data.map(e => ({ value: e.ESTADO_ABREVIADO, label: e.NOMBRE_ESTADO }));
        setEstados(options);
        const map = {}; data.forEach(e => { map[e.NOMBRE_ESTADO?.toUpperCase()] = e.ESTADO_ABREVIADO; });
        setEstadosMap(map);
        if (options.length) setSelectedEstado(options[0].value);
      } catch (e) {
        if (e.name !== 'AbortError') console.error(e);
      }
    })();
    return () => ac.abort();
  }, []);

  /* == cargar estaciones == */
  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/estaciones`, { signal: ac.signal });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        setAllStations(await r.json());
      } catch (e) {
        if (e.name !== 'AbortError') console.error(e);
      }
    })();
    return () => ac.abort();
  }, []);

  /* == aplicar filtro == */
  useEffect(() => {
    if (!selectedEstado || !allStations.length) return;
    const q = query.trim().toLowerCase();
    const [filterStart, filterEnd] = filterDateRange || [null, null];

    setFilteredStations(
      allStations.filter(est => {
        const estadoCampo = est.ESTADO?.toUpperCase();
        const matchEstado =
          estadoCampo &&
          (estadoCampo === selectedEstado.toUpperCase() || estadosMap[estadoCampo] === selectedEstado);
        const matchQuery =
          !q ||
          est.NOMBRE?.toLowerCase().includes(q) ||
          String(est.ESTACION ?? '').toLowerCase().includes(q);
        const matchAnios = !minAnios || (est.anios_de_datos && est.anios_de_datos >= minAnios);

        let matchDate = true;
        if (filterStart && filterEnd) {
          const stationStart = est.fecha_inicial_datos ? dayjs(est.fecha_inicial_datos, 'DD/MM/YYYY') : null;
          const stationEnd = est.fecha_final_datos ? dayjs(est.fecha_final_datos, 'DD/MM/YYYY') : null;
          if (!stationStart || !stationEnd) {
            matchDate = false;
          } else {
            // Overlap logic: (StartA <= EndB) and (EndA >= StartB)
            matchDate = stationStart.isBefore(filterEnd.endOf('day')) && stationEnd.isAfter(filterStart.startOf('day'));
          }
        }

        return matchEstado && matchQuery && matchAnios && matchDate;
      })
    );
  }, [selectedEstado, allStations, estadosMap, query, minAnios, filterDateRange]);

  /* == init mapa == */
  useEffect(() => {
    if (mapRef.current && !mapInstance.current) {
      const map = L.map(mapRef.current, { preferCanvas: true, zoomControl: false })
        .setView([23.6345, -102.5528], 5);
      mapInstance.current = map;

      baseLayer.current = basemaps[activeBasemap]();
      baseLayer.current.addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      markersLayer.current = L.layerGroup().addTo(map);
    }
    return () => {
      mapInstance.current?.remove();
      mapInstance.current = null;
    };
  }, []);

  /* == cambia basemap == */
  useEffect(() => {
    const map = mapInstance.current;
    if (!map) return;
    if (baseLayer.current) map.removeLayer(baseLayer.current);
    baseLayer.current = basemaps[activeBasemap]();
    baseLayer.current.addTo(map);
  }, [activeBasemap]);

  /* == pintar marcadores == */
  useEffect(() => {
    const map = mapInstance.current;
    if (!map || !markersLayer.current) return;

    markersLayer.current.clearLayers();
    markersIndex.current = {}; // <-- reset índice

    const bounds = L.latLngBounds([]);
    filteredStations.forEach(est => {
      const lat = cleanNumber(est.LATITUD);
      const lon = cleanNumber(est.LONGITUD);
      if (isNaN(lat) || isNaN(lon)) return;

      const key = `${est.ESTADO}-${est.ESTACION}`;
      const marker = L.marker([lat, lon]);

      marker.bindPopup(`<b>${est.NOMBRE ?? '—'}</b><br>${est.ESTACION ?? ''}`);
      marker.on('click', () => handleSelectStation(est));

      marker.addTo(markersLayer.current);
      markersIndex.current[key] = marker; // <-- guardamos referencia

      bounds.extend([lat, lon]);
    });
    if (fitAll && bounds.isValid()) map.fitBounds(bounds.pad(0.2));
  }, [filteredStations, fitAll]);

  /* == centrar + popup en una estación == */
  const focusStation = (station, zoom = 10) => {
    const map = mapInstance.current;
    if (!map) return;
    const lat = cleanNumber(station?.LATITUD);
    const lon = cleanNumber(station?.LONGITUD);
    if (!isNaN(lat) && !isNaN(lon)) {
      map.setView([lat, lon], zoom, { animate: true });
    }
    const key = `${station?.ESTADO}-${station?.ESTACION}`;
    const m = markersIndex.current[key];
    if (m) {
      m.openPopup();
      if (m.bringToFront) m.bringToFront();
    }
  };

  const [chartMode, setChartMode] = useState('diarios'); // 'diarios' o 'ciclo-anual'

  /* == seleccionar estación == */
  const handleSelectStation = (station) => {
    focusStation(station);
    setSelectedStation(station);
    // Al seleccionar nueva estación, volver a modo diario y setear el rango de fechas completo
    setChartMode('diarios');
    const startDate = station.fecha_inicial_datos ? dayjs(station.fecha_inicial_datos, 'DD/MM/YYYY') : null;
    const endDate = station.fecha_final_datos ? dayjs(station.fecha_final_datos, 'DD/MM/YYYY') : null;
    setDateRange([startDate, endDate]);
  };

  /* == cargar datos de la estación seleccionada (o al cambiar modo/fecha) == */
  useEffect(() => {
    if (!selectedStation) return;

    // cancelar fetch anterior (si lo hay)
    serieAbortRef.current?.abort();
    const ac = new AbortController();
    serieAbortRef.current = ac;

    setChartData(null);
    setLoadingChart(true);

    const endpointMap = {
      'diarios': 'datos',
      'ciclo-anual': 'ciclo-anual',
      'promedio-mensual': 'promedio-mensual',
      'promedio-anual': 'promedio-anual',
      'ciclo-anual-mensual': 'ciclo-anual-mensual'
    };
    const endpoint = endpointMap[chartMode] || 'datos';
    const [startDate, endDate] = dateRange;
    
    const params = new URLSearchParams();
    if (startDate) {
      // dayjs objects from antd need to be converted to JS Date before formatting
      params.append('fecha_inicio', startDate.toDate().toISOString().split('T')[0]);
    }
    if (endDate) {
      params.append('fecha_fin', endDate.toDate().toISOString().split('T')[0]);
    }
    const queryString = params.toString();

    const url = `${API_BASE}/estaciones/${selectedStation.ESTADO}/${selectedStation.ESTACION}/${endpoint}${queryString ? `?${queryString}`: ''}`;

    fetch(url, { signal: ac.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => {
        setChartData(data);
        const newVars = data?.variables ?? [];
        
        // Mantener la selección de variables si aún son válidas
        setSelectedVars(prevSelectedVars => {
          const stillValidVars = prevSelectedVars.filter(v => newVars.includes(v));
          if (stillValidVars.length > 0) {
            return stillValidVars;
          }
          // Si no, volver al default
          const defaults = newVars.filter(v => ['TMAX','TMIN'].includes(String(v).toUpperCase()));
          return defaults.length ? defaults : (newVars.length > 0 ? [newVars[0]] : []);
        });
      })
      .catch(e => { if (e.name !== 'AbortError') console.error(e); })
      .finally(() => setLoadingChart(false));
    
    return () => ac.abort();
  }, [selectedStation, chartMode, dateRange]);

  /* == botón de centrar del BottomDock (usa la estación seleccionada) == */
  const centerOnStation = () => {
    if (selectedStation) focusStation(selectedStation);
  };

  const basemapKeys = useMemo(() => Object.keys(basemaps), []);

  return (
    <div className="container">
      <SideDock
        collapsed={sideDockCollapsed}
        onToggleCollapse={() => setSideDockCollapsed(v => !v)}
        basemapKeys={basemapKeys}
        activeBasemap={activeBasemap}
        onChangeBasemap={setActiveBasemap}
        estadoOptions={estados}
        selectedEstado={selectedEstado}
        onChangeEstado={setSelectedEstado}
        query={query}
        onChangeQuery={setQuery}
        fitAll={fitAll}
        onToggleFitAll={() => setFitAll(v => !v)}
        stations={filteredStations}
        onSelectStation={handleSelectStation}   // <-- al elegir en la lista: centra + popup + series
        minAnios={minAnios}
        onChangeAnios={setMinAnios}
        filterDateRange={filterDateRange}
        onChangeFilterDateRange={setFilterDateRange}
      />
      {!sideOpen && (
          <button
            className="sidedock-toggle-btn"
            onClick={() => {
              setSideOpen(true);
              setTimeout(() => mapInstance.current?.invalidateSize?.(), 200);
            }}
            title="Mostrar panel"
            aria-label="Mostrar panel lateral"
          >
            ☰
          </button>
        )}

      <div className="map-wrap">
        <div ref={mapRef} id="map" className="map-container" />
      </div>

      <BottomDock
        open={!!selectedStation}
        station={selectedStation}
        chartData={chartData}
        loading={loadingChart}
        selectedVars={selectedVars}
        setSelectedVars={setSelectedVars}
        onCenter={centerOnStation}
        onClose={() => { 
          setSelectedStation(null); 
          setChartData(null); 
          setSelectedVars([]); 
          setDateRange([null, null]); 
        }}
        chartMode={chartMode}
        onChangeChartMode={setChartMode}
        dateRange={dateRange}
        onChangeDateRange={setDateRange}
      />
    </div>
  );
}