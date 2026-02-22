import React from 'react';

export const Logs: React.FC = () => {
  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Logs do Sistema</h1>
        <p className="page-subtitle">Monitoramento e auditoria do sistema</p>
      </div>
      
      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Logs Recentes</h2>
          </div>
          <div className="card-body">
            <div className="alert alert-info">
              Sistema de logs em desenvolvimento...
            </div>
          </div>
        </div>
      </div>
    </>
  );
};