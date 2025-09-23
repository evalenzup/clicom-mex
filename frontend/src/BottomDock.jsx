import React, { useState, useEffect, useRef } from 'react';
import { Button, Spin, Checkbox, Typography, Space } from 'antd';
import { CloseOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const { Text } = Typography;

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const BottomDock = ({ station, onClose }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedVariables, setSelectedVariables] = useState([]);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (station) {
      setLoading(true);
      fetch(`${API_BASE}/estaciones/${station.ESTADO}/${station.ESTACION}/datos`)
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then(data => {
          setChartData(data);
          setSelectedVariables(data.variables); // Select all variables by default
        })
        .catch(e => {
          console.error(e);
        })
        .finally(() => setLoading(false));
    } else {
      setChartData(null);
      setSelectedVariables([]);
    }
  }, [station]);

  useEffect(() => {
    if (chartRef.current) {
      if (!chartInstance.current) {
        chartInstance.current = echarts.init(chartRef.current);
      }
      if (chartData && selectedVariables.length > 0) {
        const options = {
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: selectedVariables
          },
          xAxis: {
            type: 'category',
            data: chartData.datos.map(d => d.Fecha)
          },
          yAxis: {
            type: 'value'
          },
          series: chartData.variables.filter(v => selectedVariables.includes(v)).map(v => ({
            name: v,
            type: 'line',
            data: chartData.datos.map(d => d[v])
          })),
          dataZoom: [
            {
              type: 'inside',
              xAxisIndex: [0],
              start: 0,
              end: 100
            },
            {
              type: 'slider',
              xAxisIndex: [0],
              start: 0,
              end: 100,
              bottom: 10
            }
          ]
        };
        chartInstance.current.setOption(options);
        chartInstance.current.resize();
      }
    }
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, [chartData, station, selectedVariables]);

  return (
    <div className={`bottom-dock ${station ? 'open' : ''}`}>
      <div className="bottom-dock-header">
        <h2 className="bottom-dock-title">{station?.NOMBRE}</h2>
        <Button icon={<CloseOutlined />} onClick={onClose} />
      </div>
      {station && (
        <Space size="middle" style={{ marginBottom: '10px', flexWrap: 'wrap' }}>
          <Text strong>{station.NOMBRE}</Text>
          <Text type="secondary">({station.ESTACION})</Text>
          <Text>{station.MUNICIPIO}, {station.ESTADO}</Text>
          <Text>Lat: {station.LATITUD}</Text>
          <Text>Lon: {station.LONGITUD}</Text>
          <Text>Situación: {station.SITUACION}</Text>
        </Space>
      )}
      {chartData && (
        <div style={{ marginBottom: '10px' }}>
          <Checkbox.Group
            options={chartData.variables.map(v => ({ label: v, value: v }))}
            value={selectedVariables}
            onChange={setSelectedVariables}
          />
        </div>
      )}
      <div className="chart-container">
        <Spin spinning={loading}>
          {chartData && <div ref={chartRef} style={{ height: '300px', width: '100%' }} />}
        </Spin>
      </div>
    </div>
  );
};

export default BottomDock;
