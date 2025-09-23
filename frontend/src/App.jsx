import React, { useState, useEffect, useRef } from 'react';
import { Select } from 'antd';
import * as L from 'leaflet';
import BottomDock from './BottomDock';
import SideDock from './SideDock';
import './App.css';
import 'leaflet/dist/leaflet.css';

const { Option } = Select;

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const App = () => {
  const [estados, setEstados] = useState([]);
  const [selectedEstado, setSelectedEstado] = useState(null);
  const [allStations, setAllStations] = useState([]);
  const [filteredStations, setFilteredStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [query, setQuery] = useState('');

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markers = useRef([]);

  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/estados`, { signal: ac.signal });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        setEstados(data);
      } catch (e) {
        if (e.name !== 'AbortError') {
          console.error(e);
        }
      }
    })();
    return () => ac.abort();
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/estaciones`, { signal: ac.signal });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        setAllStations(await r.json());
      } catch (e) {
        if (e.name !== 'AbortError') {
          console.error(e);
        }
      }
    })();
    return () => ac.abort();
  }, []);

  useEffect(() => {
    if (!selectedEstado || !allStations.length) return;

    const estadoMap = new Map(estados.map(e => [e.NOMBRE_ESTADO.toUpperCase(), e.ESTADO_ABREVIADO.toUpperCase()]));

    const q = query.trim().toLowerCase();
    setFilteredStations(
      allStations.filter(est => {
        const abbreviatedEstado = estadoMap.get(est.ESTADO?.toUpperCase());
        const matchEstado = abbreviatedEstado === selectedEstado.toUpperCase();
        const matchQuery = !q || est.NOMBRE?.toLowerCase().includes(q) || String(est.ESTACION ?? '').toLowerCase().includes(q);
        return matchEstado && matchQuery;
      })
    );
  }, [selectedEstado, allStations, query, estados]);

  useEffect(() => {
    if (mapRef.current && !mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, { preferCanvas: true, zoomControl: false }).setView([23.6345, -102.5528], 5);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(mapInstance.current);
      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance.current);
      mapInstance.current.invalidateSize();
    }
    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapInstance.current) return;
    markers.current.forEach(m => m.remove());
    markers.current = [];

    const bounds = L.latLngBounds([]);
    filteredStations.forEach(est => {
      const lat = parseFloat(String(est.LATITUD).replace(',', '.'));
      const lon = parseFloat(String(est.LONGITUD).replace(',', '.'));
      if (isNaN(lat) || isNaN(lon)) return;
      const marker = L.marker([lat, lon]).addTo(mapInstance.current);
      marker.bindPopup(`<b>${est.NOMBRE ?? '—'}</b><br>${est.ESTACION ?? ''}`);
      marker.on('click', () => setSelectedStation(est));
      markers.current.push(marker);
      bounds.extend([lat, lon]);
    });
    if (bounds.isValid()) mapInstance.current.fitBounds(bounds.pad(0.2));
  }, [filteredStations]);

  return (
    <div className="container">
      <SideDock
        estados={estados}
        selectedEstado={selectedEstado}
        setSelectedEstado={setSelectedEstado}
        query={query}
        setQuery={setQuery}
        filteredStations={filteredStations}
        selectedStation={selectedStation}
        setSelectedStation={setSelectedStation}
      />
      <div className="map-container" ref={mapRef} />
      <BottomDock station={selectedStation} onClose={() => setSelectedStation(null)} />
    </div>
  );
};

export default App;
