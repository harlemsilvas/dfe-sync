import React, { useState, useEffect } from 'react';
import { adminApi } from '../api/admin';

interface DashboardStats {
  total_xmls: number;
  empresas_cadastradas: number;
  xmls_classificados: number;
  xmls_pendentes: number;
  certificados_validos: number;
  certificados_vencendo: number;
  operacoes_pendentes?: number;
  ultima_atualizacao?: string;
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
      setError('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Carregando estatísticas...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-state">
        <h2>⚠️ Erro</h2>
        <p>{error}</p>
        <button onClick={loadStats} className="btn btn-primary">
          Tentar Novamente
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="content-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Visão geral do sistema DFE Sync</p>
          {stats?.ultima_atualizacao && (
            <small style={{color: '#666'}}>
              Última atualização: {new Date(stats.ultima_atualizacao).toLocaleString('pt-BR')}
            </small>
          )}
        </div>
        <button onClick={loadStats} className="btn btn-secondary" disabled={loading}>
          {loading ? '🔄 Atualizando...' : '🔄 Atualizar'}
        </button>
      </div>
      
      <div className="content-body">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats?.total_xmls || 0}</div>
            <div className="stat-label">Total de XMLs</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-number">{stats?.empresas_cadastradas || 0}</div>
            <div className="stat-label">Empresas Cadastradas</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-number">{stats?.xmls_classificados || 0}</div>
            <div className="stat-label">XMLs Classificados</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-number">{stats?.xmls_pendentes || 0}</div>
            <div className="stat-label">XMLs Pendentes</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-number">{stats?.certificados_validos || 0}</div>
            <div className="stat-label">Certificados Válidos</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-number">{stats?.certificados_vencendo || 0}</div>
            <div className="stat-label">Certificados Vencendo</div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Ações Rápidas</h2>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
              <a href="/importacao" className="btn btn-primary">
                📁 Importar XMLs
              </a>
              <a href="/classificacao" className="btn btn-warning">
                🔄 Classificar Pendentes
              </a>
              <a href="/empresas" className="btn btn-success">
                🏢 Cadastrar Empresa
              </a>
              <a href="/certificados" className="btn btn-info">
                🔐 Gerenciar Certificados
              </a>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Status do Sistema</h2>
          </div>
          <div className="card-body">
            <div className="alert alert-success">
              ✅ Sistema DFE Sync operacional
            </div>
            <div className="alert alert-info">
              ℹ️ Última sincronização: {new Date().toLocaleString()}
            </div>
            {stats?.certificados_vencendo && stats.certificados_vencendo > 0 && (
              <div className="alert alert-warning">
                ⚠️ {stats.certificados_vencendo} certificado(s) vencendo em breve
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};