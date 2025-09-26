import React, { useState } from 'react';

/**
 * SideDock colapsable, compacto, estilo Windy.
 */
export default function SideDock({
  collapsed,
  onToggleCollapse,
  basemapKeys,
  activeBasemap,
  onChangeBasemap,
  estadoOptions,
  selectedEstado,
  onChangeEstado,
  query,
  onChangeQuery,
  fitAll,
  onToggleFitAll,
  stations,
  onSelectStation,
}) {
  return (
    <aside className={`sidedock ${collapsed ? 'sidedock--collapsed' : ''}`}>
      <div className="sidedock__topbar">
        <button
          className="icon-btn"
          title={collapsed ? 'Expandir' : 'Colapsar'}
          onClick={onToggleCollapse}
        >
          ☰
        </button>
        {!collapsed && <div className="sidedock__title">Visor de Estaciones</div>}
      </div>

      {!collapsed && (
        <div className="sidedock__content glass">
          <div className="sidedock__row">
            <label className="label">Estado</label>
            <select
              className="input"
              value={selectedEstado ?? ''}
              onChange={(e) => onChangeEstado(e.target.value || null)}
            >
              {estadoOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="sidedock__row">
            <label className="label">Buscar</label>
            <div className="pill">
              <span>🔎</span>
              <input
                className="pill__input"
                placeholder="Nombre o clave…"
                value={query}
                onChange={(e) => onChangeQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="sidedock__row">
            <label className="label">Mapa base</label>
            <div className="chips">
              {basemapKeys.map(k => (
                <button
                  key={k}
                  className={`chip ${activeBasemap === k ? 'chip--active' : ''}`}
                  onClick={() => onChangeBasemap(k)}
                >
                  {k}
                </button>
              ))}
            </div>
          </div>

          <div className="sidedock__row">
            <div className="chips">
              <button className={`chip ${fitAll ? 'chip--active' : ''}`} onClick={onToggleFitAll}>
                {fitAll ? 'Auto-fit ON' : 'Auto-fit OFF'}
              </button>
              <div className="card">
                <div className="card__label">Estaciones visibles</div>
                <div className="card__value">{stations.length}</div>
              </div>
            </div>
          </div>

          <div className="sidedock__list">
            <ul className="station-list">
              {stations.map((est) => (
                <li
                  key={`${est.ESTADO}-${est.ESTACION}`}
                  className="station-item"
                  onClick={() => onSelectStation(est)}
                  title={est.NOMBRE}
                >
                  <div className="station-item__name">{est.NOMBRE ?? '—'}</div>
                  <div className="station-item__meta">
                    <span className="badge">{est.ESTACION ?? '—'}</span>
                    <span className="badge">{est.ESTADO ?? '—'}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </aside>
  );
}