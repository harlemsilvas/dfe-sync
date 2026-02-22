import React from 'react';

export const Relatorios: React.FC = () => {
  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Relatórios</h1>
        <p className="page-subtitle">Relatórios e estatísticas do sistema</p>
      </div>
      
      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Relatórios Disponíveis</h2>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">📊</div>
                <div className="stat-label">Dashboard Executivo</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">📈</div>
                <div className="stat-label">Relatório de Importação</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">📋</div>
                <div className="stat-label">Relatório de Classificação</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};