import React, { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import * as echarts from 'echarts';
import { DatePicker, Button } from 'antd';
import { AimOutlined, DownloadOutlined, CloseOutlined } from '@ant-design/icons';

import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
dayjs.extend(customParseFormat);

const { RangePicker } = DatePicker;

const PALETTE = ['#5ad8a6','#5b8ff9','#f6bd16','#e8684a','#6dc8ec','#9270ca','#ff9d4d'];
const norm = s => String(s || '').trim().toUpperCase();

const isTemp = (v) => ['T','TMP','TEMP','TEMPERATURA','TMAX','TMIN', 'TPROM', 'TRANGO'].includes(norm(v));
const isTmax = (v) => norm(v) === 'TMAX';
const isTmin = (v) => norm(v) === 'TMIN';

const isEvap = (v) => ['EVAP','EVAPORACION','EVAPORACIÓN'].includes(norm(v));
const isPrecip = (v) => ['PRECIP','PRECIPITACION','PRECIPITACIÓN','PP','PPT'].includes(norm(v));

const unitForVar = (v) => (isTmax(v) || isTmin(v)) ? '°C' : (isPrecip(v) || isEvap(v)) ? 'mm' : '';

export default function BottomDock({
  open,
  station,
  chartData,
  loading,
  selectedVars,
  setSelectedVars,
  onCenter,
  onClose,
  chartMode,
  onChangeChartMode,
  dateRange,
  onChangeDateRange,
}) {
  const chartRef = useRef(null);
  const chart = useRef(null);
  const roRef = useRef(null);

  const handleDownloadChart = () => {
    if (!chart.current) return;
    const url = chart.current.getDataURL({
      type: 'jpeg',
      backgroundColor: '#1f2937', // Un color de fondo oscuro para el JPG
      pixelRatio: 2, // Exportar a mayor resolución
    });
    const link = document.createElement('a');
    const stationName = station?.NOMBRE?.replace(/\s+/g, '_') || station?.ESTACION;
    link.download = `grafica-${stationName}.jpg`;
    link.href = url;
    link.click();
  };

  const toggleVar = (v) => {
    setSelectedVars(prev => prev.includes(v) ? prev.filter(x => x !== v) : [...prev, v]);
  };

  useLayoutEffect(() => {
    const el = chartRef.current;
    const wrap = el?.parentElement;
    if (!el || !wrap) return;

    let disposed = false;
    let raf = 0;

    const tryInit = () => {
      if (disposed) return;
      const { clientWidth: w, clientHeight: h } = el;
      if (w > 0 && h > 0) {
        chart.current = echarts.init(el);
        const ro = new ResizeObserver(() => chart.current?.resize());
        ro.observe(wrap);
        roRef.current = ro;
      } else {
        raf = requestAnimationFrame(tryInit);
      }
    };

    raf = requestAnimationFrame(tryInit);
    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      roRef.current?.disconnect();
      roRef.current = null;
      chart.current?.dispose();
      chart.current = null;
    };
  }, []);

  useEffect(() => {
    if (chart.current) requestAnimationFrame(() => chart.current?.resize());
  }, [open, loading]);

  // ===== Ajuste automático de ejes Y en función de las variables visibles =====
  const yAxesInfo = useMemo(() => {
    const allVars = chartData?.variables ?? [];
    const datos = chartData?.datos ?? [];
    const vars = (selectedVars?.length ? allVars.filter(v => selectedVars.includes(v)) : []);
    if (!vars.length || !datos.length) return { axes: [], mapIdx: {}, unitByAxis: {} };

    const axes = [];
    const mapIdx = {};
    const unitByAxis = {};

    const seriesVals = (names) => {
      const all = [];
      datos.forEach(d => {
        names.forEach(n => {
          const v = Number(d[n]);
          if (Number.isFinite(v)) all.push(v);
        });
      });
      return all.length ? all : [0, 1];
    };

    // 🔧 helper de formato con máx 2 decimales para el eje
    const fmt2 = (val) => {
      if (!Number.isFinite(val)) return val;
      return Number(val).toLocaleString('en-US', { maximumFractionDigits: 2 });
    };

    const mkAxis = (values, unit, forceZero = false) => {
      let min = Math.min(...values), max = Math.max(...values);
      if (min === max) { min -= 1; max += 1; }
      const pad = (max - min) * 0.06;
      let axisMin = forceZero ? 0 : min - pad;
      let axisMax = max + pad;
      return {
        def: {
          type: 'value',
          min: axisMin,
          max: axisMax,
          name: unit || '',
          nameTextStyle: { color: '#c9d3e3' },
          // 👇 Mostrar máximo 2 decimales en las etiquetas
          axisLabel: {
            color: '#c9d3e3',
            formatter: (value) => unit ? `${fmt2(value)} ${unit}` : fmt2(value),
          },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } }
        },
        unit,
      };
    };

    // Grupo temperaturas (TMAX/TMIN) — sólo si alguno está visible
    const tempVars = vars.filter(v => isTmax(v) || isTmin(v));
    if (tempVars.length) {
      const values = seriesVals(tempVars);
      const { def, unit } = mkAxis(values, '°C');
      const idx = axes.length;
      axes.push(def);
      unitByAxis[idx] = unit;
      tempVars.forEach(v => (mapIdx[v] = idx));
    }

    // Grupo hidro (PRECIP/EVAP) con min=0 — sólo si alguno está visible
    const hydroVars = vars.filter(v => isPrecip(v) || isEvap(v));
    if (hydroVars.length) {
      const values = seriesVals(hydroVars);
      const { def, unit } = mkAxis(values, 'mm', true); // fuerza min = 0
      const idx = axes.length;
      axes.push(def);
      unitByAxis[idx] = unit;
      hydroVars.forEach(v => (mapIdx[v] = idx));
    }

    // Resto de visibles: eje individual
    vars.forEach(v => {
      if (mapIdx[v] != null) return;
      const values = seriesVals([v]);
      const { def, unit } = mkAxis(values, unitForVar(v));
      const idx = axes.length;
      axes.push(def);
      unitByAxis[idx] = unit;
      mapIdx[v] = idx;
    });

    return { axes, mapIdx, unitByAxis };
  }, [chartData, selectedVars]);

  useEffect(() => {
    if (!chart.current) return;

    const vars = chartData?.variables ?? [];
    const datos = chartData?.datos ?? [];

    if (!vars.length || !datos.length) {
      chart.current.clear();
      return;
    }

    const visible = selectedVars.filter(v => vars.includes(v));

    if (visible.length === 0) {
      chart.current.clear();
      return;
    }

    const series = visible.map((name) => ({
      name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      sampling: 'lttb',
      yAxisIndex: yAxesInfo.mapIdx[name] ?? 0,
      lineStyle: { width: 2.2 },
      // 🔧 Anti-flicker:
      emphasis: { disabled: true },
      hoverAnimation: false,
      blendMode: 'source-over',
      data: datos.map(d => {
        const v = Number(d[name]);
        // Para temperaturas, no graficar los ceros (suelen ser datos faltantes)
        if (isTemp(name) && v === 0) return null;
        return Number.isFinite(v) ? v : null;
      }),
      itemStyle: { color: PALETTE[vars.indexOf(name) % PALETTE.length] },
    }));

    chart.current.setOption({
      // 🔧 Anti-flicker global:
      animation: false,
      animationDurationUpdate: 0,
      animationEasingUpdate: 'linear',

      color: PALETTE,
      backgroundColor: 'transparent',
      grid: { left: 56, right: 24, top: 10, bottom: 52 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'line', animation: false, snap: true },
        transitionDuration: 0,
        backgroundColor: '#ffffff',
        borderColor: 'rgba(0,0,0,0.10)',
        textStyle: { color: '#111', fontWeight: 600 },
        extraCssText: 'box-shadow:0 8px 24px rgba(0,0,0,.25); border-radius:12px; padding:10px 12px;',
        formatter: (params) => {
          if (!params?.length) return '';
          const date = params[0].axisValueLabel ?? '';
          const rows = params.map(p => {
            const u = unitForVar(p.seriesName);
            const val = (p.value == null || Number.isNaN(p.value)) ? '—' : `${p.value} ${u}`;
            return `<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
              <span style="display:flex;align-items:center;gap:6px;">${p.marker}<span>${p.seriesName}</span></span>
              <b>${val}</b>
            </div>`;
          }).join('');
          return `<div style="min-width:180px">
            <div style="opacity:.8;margin-bottom:6px">${date}</div>
            ${rows}
          </div>`;
        }
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: datos.map(d => {
          if (chartMode === 'ciclo-anual') return d.dia_mes;
          if (chartMode === 'ciclo-anual-mensual') {
            const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
            return monthNames[d.Mes - 1];
          }
          return d.Fecha;
        }),
        axisLabel: { color: '#c9d3e3', hideOverlap: true },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.25)' } },
        axisTick: { alignWithLabel: true },
      },
      yAxis: yAxesInfo.axes,
      dataZoom: [
        { type: 'inside', zoomOnMouseWheel: true, moveOnMouseWheel: true },
        { type: 'slider', height: 22, bottom: 20, start: 80, end: 100, brushSelect: false }
      ],
      series,
    }, { notMerge: true, lazyUpdate: false });

    chart.current.resize();
  }, [chartData, selectedVars, yAxesInfo]);

  const fmtCoord = (v) => {
    const n = Number(String(v).replace(/[^\d\-\.\,]/g, '').replace(',', '.'));
    return Number.isFinite(n) ? n.toFixed(3) : '—';
  };
  const fmtAlt = (v) => {
    const n = Number(String(v).replace(/[^\d\-\.\,]/g, '').replace(',', '.'));
    return Number.isFinite(n) ? `${n} msnm` : (v ?? '—');
  };

  const disabledDate = (current) => {
    if (!station?.fecha_inicial_datos || !station?.fecha_final_datos) return false;
    const minDate = dayjs(station.fecha_inicial_datos, 'DD/MM/YYYY');
    const maxDate = dayjs(station.fecha_final_datos, 'DD/MM/YYYY');
    return current < minDate || current > maxDate;
  };

  return (
    <div className={`bottom-dock ${open ? 'open' : ''}`}>
      <div className="bottom-dock__inner glass-strong">
        <div className="bottom-dock-header">
          <div className="bottom-dock-title">
            <span className="muted">Estación</span>
            <span className="ellipsis">{station?.NOMBRE ?? '—'}</span>
            <span className="badge">{station?.ESTACION ?? '—'}</span>
            <span className="badge">{station?.ESTADO ?? '—'}</span>
            <span className="badge" title="Ubicación">
              {fmtCoord(station?.LATITUD)}, {fmtCoord(station?.LONGITUD)} · {fmtAlt(station?.ALTITUD)}
            </span>
            <span className="badge" title="Periodo de datos">
              {station?.fecha_inicial_datos || '—'} - {station?.fecha_final_datos || '—'}
            </span>
          </div>
          <div className="bottom-dock-toolbar">
            <Button type="default" shape="circle" icon={<AimOutlined />} onClick={onCenter} title="Centrar en mapa" />
            <Button type="default" shape="circle" icon={<DownloadOutlined />} onClick={handleDownloadChart} title="Descargar Gráfica" />
            <Button type="default" shape="circle" icon={<CloseOutlined />} onClick={onClose} title="Cerrar" />
          </div>
        </div>

        <div className="bottom-dock-body">
          <div className="chart-fixed">
            {loading && <div className="loader">Cargando datos…</div>}
            <div ref={chartRef} className="chart-container" />
          </div>

          <div className="controls-block" style={{ display: 'flex', alignItems: 'flex-start', gap: '24px' }}>
            <div className="control-group">
              <label className="label" style={{ marginBottom: '8px', display: 'block' }}>Variables</label>
              <div className="series-tabs">
                {(chartData?.variables ?? []).map((s) => {
                  const active = selectedVars.includes(s);
                  return (
                    <button
                      key={s}
                      className={`chip ${active ? 'chip--active' : ''}`}
                      onClick={() => toggleVar(s)}
                      title={s}
                      // 🎨 Más contraste cuando está activa
                      style={active ? {
                        background: PALETTE[(chartData?.variables ?? []).indexOf(s) % PALETTE.length],
                        color: '#0b0f14',
                        borderColor: 'transparent',
                        boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.15)'
                      } : {}}
                    >
                      {s}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="control-group">
              <label className="label" style={{ marginBottom: '8px', display: 'block' }}>Tipo Gráfica</label>
              <div className="chart-modes">
                <button
                  className={`chip ${chartMode === 'diarios' ? 'chip--active' : ''}`}
                  onClick={() => onChangeChartMode('diarios')}
                  style={chartMode === 'diarios' ? { background: '#5ad8a6', color: '#fff' } : {}}
                >
                  Diarios
                </button>
                <button
                  className={`chip ${chartMode === 'promedio-mensual' ? 'chip--active' : ''}`}
                  onClick={() => onChangeChartMode('promedio-mensual')}
                  style={chartMode === 'promedio-mensual' ? { background: '#5ad8a6', color: '#fff' } : {}}
                >
                  Promedio Mensual
                </button>
                <button
                  className={`chip ${chartMode === 'promedio-anual' ? 'chip--active' : ''}`}
                  onClick={() => onChangeChartMode('promedio-anual')}
                  style={chartMode === 'promedio-anual' ? { background: '#5ad8a6', color: '#fff' } : {}}
                >
                  Promedio Anual
                </button>
                <button
                  className={`chip ${chartMode === 'ciclo-anual' ? 'chip--active' : ''}`}
                  onClick={() => onChangeChartMode('ciclo-anual')}
                  style={chartMode === 'ciclo-anual' ? { background: '#5ad8a6', color: '#fff' } : {}}
                >
                  Ciclo Anual (Diario)
                </button>
                <button
                  className={`chip ${chartMode === 'ciclo-anual-mensual' ? 'chip--active' : ''}`}
                  onClick={() => onChangeChartMode('ciclo-anual-mensual')}
                  style={chartMode === 'ciclo-anual-mensual' ? { background: '#5ad8a6', color: '#fff' } : {}}
                >
                  Ciclo Anual (Mensual)
                </button>
              </div>
            </div>
            <div className="control-group">
              <label className="label" style={{ marginBottom: '8px', display: 'block' }}>Periodo</label>
              <RangePicker 
                value={dateRange}
                disabledDate={disabledDate}
                onChange={(dates) => {
                  onChangeDateRange(dates ? [dates[0], dates[1]] : [null, null]);
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}