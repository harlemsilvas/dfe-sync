import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';

interface Empresa {
  id: number;
  cnpj: string;
  razao_social: string;
  nome_fantasia?: string;
  monitorada: boolean;
  pasta_origem?: string;
  ativo: boolean;
  created_at: string;
  updated_at: string;
}

export const Empresas: React.FC = () => {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingEmpresa, setEditingEmpresa] = useState<Empresa | null>(null);
  const [showDirBrowser, setShowDirBrowser] = useState(false);
  const [currentPath, setCurrentPath] = useState('/');
  const [directorios, setDirectorios] = useState<any[]>([]);
  const [loadingDir, setLoadingDir] = useState(false);
  const [formData, setFormData] = useState({
    cnpj: '',
    razao_social: '',
    nome_fantasia: '',
    monitorada: true,
    pasta_origem: '',
    ativo: true,
  });

  useEffect(() => {
    loadEmpresas();
  }, []);

  const loadEmpresas = async () => {
    try {
      const data = await adminApi.getEmpresas();
      setEmpresas(data);
    } catch (error) {
      console.error('Erro ao carregar empresas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingEmpresa) {
        await adminApi.updateEmpresa(editingEmpresa.id, formData);
      } else {
        await adminApi.createEmpresa(formData);
      }
      await loadEmpresas();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar empresa:', error);
    }
  };

  const handleEdit = (empresa: Empresa) => {
    setEditingEmpresa(empresa);
    setFormData({
      cnpj: empresa.cnpj,
      razao_social: empresa.razao_social,
      nome_fantasia: empresa.nome_fantasia || '',
      monitorada: empresa.monitorada,
      pasta_origem: empresa.pasta_origem || '',
      ativo: empresa.ativo,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Tem certeza que deseja excluir esta empresa?')) {
      try {
        await adminApi.deleteEmpresa(id);
        await loadEmpresas();
      } catch (error) {
        console.error('Erro ao excluir empresa:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      cnpj: '',
      razao_social: '',
      nome_fantasia: '',
      monitorada: true,
      pasta_origem: '',
      ativo: true,
    });
    setEditingEmpresa(null);
    setShowForm(false);
  };

  const formatCNPJ = (cnpj: string) => {
    return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
  };

  const loadDirectorios = async (caminho: string = '/') => {
    setLoadingDir(true);
    try {
      const response = await adminApi.buscarDiretorios(caminho);
      setDirectorios(response.diretorios || []);
      setCurrentPath(response.caminho_atual);
    } catch (error) {
      console.error('Erro ao carregar diretórios:', error);
      alert('Erro ao carregar diretórios');
    } finally {
      setLoadingDir(false);
    }
  };

  const handleSelectDirectory = (dir: any) => {
    if (dir.tipo === 'diretorio' || dir.tipo === 'voltar') {
      loadDirectorios(dir.caminho);
    }
  };

  const handleUseDirectory = () => {
    setFormData({ ...formData, pasta_origem: currentPath });
    setShowDirBrowser(false);
  };

  const handleDeleteEmpresa = async (empresa: Empresa) => {
    if (!confirm(`Deseja realmente excluir a empresa ${empresa.razao_social}?`)) {
      return;
    }
    
    try {
      await adminApi.deleteEmpresa(empresa.id);
      alert('Empresa excluída com sucesso!');
      loadEmpresas();
    } catch (error) {
      console.error('Erro ao excluir empresa:', error);
      alert('Erro ao excluir empresa');
    }
  };

  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Gestão de Empresas</h1>
        <p className="page-subtitle">Cadastro e gerenciamento de empresas monitoradas</p>
      </div>
      
      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Empresas Cadastradas</h2>
            <button 
              className="btn btn-primary" 
              onClick={() => setShowForm(true)}
            >
              🏢 Nova Empresa
            </button>
          </div>
          
          <div className="card-body">
            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>CNPJ</th>
                      <th>Razão Social</th>
                      <th>Nome Fantasia</th>
                      <th>Monitorada</th>
                      <th>Pasta Origem</th>
                      <th>Status</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {empresas.map((empresa) => (
                      <tr key={empresa.id}>
                        <td>{formatCNPJ(empresa.cnpj)}</td>
                        <td>{empresa.razao_social}</td>
                        <td>{empresa.nome_fantasia || '-'}</td>
                        <td>
                          <span className={`badge ${empresa.monitorada ? 'badge-success' : 'badge-warning'}`}>
                            {empresa.monitorada ? 'Sim' : 'Não'}
                          </span>
                        </td>
                        <td>{empresa.pasta_origem || '-'}</td>
                        <td>
                          <span className={`badge ${empresa.ativo ? 'badge-success' : 'badge-danger'}`}>
                            {empresa.ativo ? 'Ativo' : 'Inativo'}
                          </span>
                        </td>
                        <td>
                          <button 
                            className="btn btn-sm btn-warning"
                            onClick={() => handleEdit(empresa)}
                            title="Editar empresa"
                          >
                            ✏️
                          </button>
                          <button 
                            className="btn btn-sm btn-danger"
                            onClick={() => handleDeleteEmpresa(empresa)}
                            style={{ marginLeft: '8px' }}
                            title="Excluir empresa"
                          >
                            🗑️
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {showForm && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                {editingEmpresa ? 'Editar Empresa' : 'Nova Empresa'}
              </h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">CNPJ *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={formData.cnpj}
                        onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
                        placeholder="00.000.000/0000-00"
                        required
                      />
                    </div>
                  </div>
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">Razão Social *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={formData.razao_social}
                        onChange={(e) => setFormData({ ...formData, razao_social: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">Nome Fantasia</label>
                      <input
                        type="text"
                        className="form-control"
                        value={formData.nome_fantasia}
                        onChange={(e) => setFormData({ ...formData, nome_fantasia: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">Pasta de Origem</label>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <input
                          type="text"
                          className="form-control"
                          value={formData.pasta_origem}
                          onChange={(e) => setFormData({ ...formData, pasta_origem: e.target.value })}
                          placeholder="/caminho/para/pasta"
                          style={{ flex: 1 }}
                        />
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => {
                            setShowDirBrowser(true);
                            loadDirectorios(formData.pasta_origem || '/');
                          }}
                        >
                          📁 Buscar
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">
                        <input
                          type="checkbox"
                          checked={formData.monitorada}
                          onChange={(e) => setFormData({ ...formData, monitorada: e.target.checked })}
                          style={{ marginRight: '8px' }}
                        />
                        Empresa Monitorada
                      </label>
                    </div>
                  </div>
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">
                        <input
                          type="checkbox"
                          checked={formData.ativo}
                          onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                          style={{ marginRight: '8px' }}
                        />
                        Empresa Ativa
                      </label>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-secondary" onClick={resetForm}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {editingEmpresa ? 'Atualizar' : 'Cadastrar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal Navegador de Diretórios */}
        {showDirBrowser && (
          <div className="modal-overlay" onClick={() => setShowDirBrowser(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Selecionar Pasta de Origem</h3>
                <button className="btn btn-sm btn-secondary" onClick={() => setShowDirBrowser(false)}>
                  ✕
                </button>
              </div>
              <div className="modal-body">
                <div style={{ marginBottom: '15px' }}>
                  <strong>Caminho atual:</strong> {currentPath}
                </div>
                
                {loadingDir ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <p>Carregando diretórios...</p>
                  </div>
                ) : (
                  <div className="directory-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {directorios.map((dir, index) => (
                      <div 
                        key={index}
                        className="directory-item"
                        style={{
                          padding: '10px',
                          borderBottom: '1px solid #eee',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                        onClick={() => handleSelectDirectory(dir)}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <span style={{ marginRight: '10px' }}>
                          {dir.tipo === 'voltar' ? '⬅️' : '📁'}
                        </span>
                        <span>{dir.nome}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowDirBrowser(false)}>
                  Cancelar
                </button>
                <button className="btn btn-primary" onClick={handleUseDirectory}>
                  Usar Este Diretório
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};