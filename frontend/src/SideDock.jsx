import React from 'react';
import { Select, Input } from 'antd';

const { Option } = Select;
const { Search } = Input;

const SideDock = ({
  estados,
  selectedEstado,
  setSelectedEstado,
  query,
  setQuery,
  filteredStations,
  selectedStation,
  setSelectedStation,
}) => {
  return (
    <div className="sidebar">
      <h1 className="title">Visor de Estaciones</h1>
      <Select
        value={selectedEstado}
        onChange={setSelectedEstado}
        style={{ width: '100%', marginBottom: 20 }}
        placeholder="Selecciona un estado"
      >
        {estados.map(e => (
          <Option key={e.ESTADO_ABREVIADO} value={e.ESTADO_ABREVIADO}>{e.NOMBRE_ESTADO}</Option>
        ))}
      </Select>
      <Search
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Buscar estación (nombre o clave)"
        className="search-input"
      />
      <ul className="station-list">
        {filteredStations.map(est => (
          <li
            key={`${est.ESTADO}-${est.ESTACION}`}
            className={`station-item ${selectedStation?.ESTACION === est.ESTACION ? 'active' : ''}`}
            onClick={() => setSelectedStation(est)}
          >
            {est.NOMBRE}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SideDock;