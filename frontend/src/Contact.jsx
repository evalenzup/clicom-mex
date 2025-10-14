
import React from 'react';

export default function Contact({ onClose }) {
  return (
    <div className="contact-overlay">
      <div className="contact-card glass">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>Contacto</h2>
        <div className="contact-content">
          <p>
            <strong>Ing. Ernesto Valenzuela</strong><br />
            <a href="mailto:evalenzu@cicese.mx">evalenzu@cicese.mx</a><br />
            Ext. 24074
          </p>
          <p>
            <strong>Dra. Tereza Cavazos</strong><br />
            <a href="mailto:tcavazos@cicese.mx">tcavazos@cicese.mx</a><br />
            Ext. 24049<br />
            <a href="http://usuario.cicese.mx/~tcavazos/" target="_blank" rel="noopener noreferrer">http://usuario.cicese.mx/~tcavazos/</a>
          </p>
          <hr />
          <p>
            <strong>Departamento de Oceanografía Física</strong><br />
            División de Oceanología<br />
            CICESE
          </p>
          <p>
            Carretera Ensenada-Tijuana No. 3918, Zona Playitas, C.P. 22860, Ensenada, B.C. Mexico.
          </p>
          <p>
            Teléfono: 01(646)175-05-00
          </p>
        </div>
      </div>
    </div>
  );
}
