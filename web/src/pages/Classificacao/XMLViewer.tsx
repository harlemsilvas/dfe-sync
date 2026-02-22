import React from 'react';
import { useParams } from 'react-router-dom';

export const XMLViewer: React.FC = () => {
  const { id } = useParams();

  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Visualizador de XML</h1>
        <p className="page-subtitle">Visualização detalhada do documento XML</p>
      </div>
      
      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">XML ID: {id}</h2>
          </div>
          <div className="card-body">
            <p>Funcionalidade em desenvolvimento...</p>
          </div>
        </div>
      </div>
    </>
  );
};