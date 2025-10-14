
import React from 'react';

export default function Info({ onClose }) {
  return (
    <div className="contact-overlay">
      <div className="contact-card glass">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>Información</h2>
        <div className="contact-content" style={{ maxHeight: '80vh', overflowY: 'auto' }}>
          <h4>Base de Datos y Origen</h4>
          <p>
            Esta página utiliza una base de datos de estaciones climáticas superficiales de México, 
            administrada por el <strong>Lic. Alejandro González Serratos</strong> del Servicio Meteorológico Nacional (SMN).
            El sistema <strong>CLICOM</strong> (CLImate COMputing project), desarrollado por las Naciones Unidas, 
            es la base para el manejo de estos datos climatológicos.
          </p>
          <p>
            Las observaciones diarias del CLICOM representan los datos recopilados durante las 24 horas previas a las 8:00 AM. 
            Los periodos de información varían por estación, con registros que pueden extenderse desde <strong>1920 hasta 2022</strong>.
          </p>

          <h4>Propósito y Funcionalidades</h4>
          <p>
            El objetivo de esta herramienta web, desarrollada en CICESE, es facilitar el procesamiento y la visualización de los 
            datos diarios del sistema CLICOM en su formato original de estaciones puntuales.
          </p>
          <p>
            Nuestra interface permite:
            <ul>
              <li>
                <strong>Visualización Interactiva:</strong> Explore las estaciones climáticas seleccionando un estado y luego una estación 
                directamente en el mapa, o buscando por su nombre.
              </li>
              <li>
                <strong>Filtrado Avanzado:</strong> Seleccione estaciones según la cantidad de años de datos disponibles o un rango de fechas específico.
              </li>
              <li>
                <strong>Análisis Gráfico:</strong> Genere y descargue gráficas de ciclo anual y series de tiempo para variables como 
                temperaturas, precipitación, evaporación y unidades de calor.
              </li>
              <li>
                <strong>Exportación de Datos:</strong> Descargue los datos de las gráficas en formato de texto para su propio análisis.
              </li>
            </ul>
          </p>

          <h4>Futuras Mejoras</h4>
          <p>
            Planeamos incluir variables adicionales para el estudio de eventos extremos, como la frecuencia de heladas, 
            ondas de calor y precipitaciones intensas, así como sus umbrales.
          </p>

          <h4>Financiamiento y Control de Calidad</h4>
          <p>
            El desarrollo de esta página es parcialmente financiado por el <strong>CICESE</strong>. Es importante aclarar que el SMN 
            realiza un control de calidad inicial sobre la base de datos del CLICOM.
          </p>

          <h4>Datos Recientes y Otras Fuentes</h4>
          <p>
            Para datos meteorológicos e hidrométricos diarios más recientes, consulte la plataforma de la 
            Subdirección Técnica de <strong>CONAGUA</strong>: <a href="http://sih.conagua.gob.mx" target="_blank" rel="noopener noreferrer">sih.conagua.gob.mx</a>.
          </p>
          <p>
            El <strong>SMN</strong> también ofrece datos semidiarios de Estaciones Meteorológicas Automáticas (EMAS) en: 
            <a href="https://smn.conagua.gob.mx/es/observando-el-tiempo/estaciones-meteorologicas-automaticas-ema-s" target="_blank" rel="noopener noreferrer">smn.conagua.gob.mx</a>.
          </p>

          <h4>Cómo Citar</h4>
          <p>
            Datos climáticos diarios del CLICOM del SMN a través de su plataforma web del CICESE: 
            <a href="http://clicom-mex.cicese.mx" target="_blank" rel="noopener noreferrer">clicom-mex.cicese.mx</a>.
          </p>
          <p>
            Para ver estudios que han utilizado estos datos, busque en Google Scholar: 
            <a href="https://scholar.google.com/scholar?q=clicom-mex.cicese.mx" target="_blank" rel="noopener noreferrer">citas de clicom-mex.cicese.mx</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
