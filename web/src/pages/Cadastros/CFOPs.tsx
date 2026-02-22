import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';

interface CFOP {
  id: number;
  codigo: string;
  descricao: string;
  tipo_operacao: string;
  transferencia: boolean;
  ativo: boolean;
}

export const CFOPs: React.FC = () => {
  const [cfops, setCfops] = useState<CFOP[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCfop, setEditingCfop] = useState<CFOP | null>(null);
  const [formData, setFormData] = useState({
    codigo: '',
    descricao: '',
    tipo_operacao: 'ENTRADA',
    transferencia: false,
    ativo: true,
  });

  useEffect(() => {
    loadCfops();
  }, []);

  const loadCfops = async () => {
    try {
      const data = await adminApi.getCFOPs();
      setCfops(data);
    } catch (error) {
      console.error('Erro ao carregar CFOPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingCfop) {
        await adminApi.updateCFOP(editingCfop.id, formData);
      } else {
        await adminApi.createCFOP(formData);
      }
      await loadCfops();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar CFOP:', error);
    }
  };

  const handleEdit = (cfop: CFOP) => {
    setEditingCfop(cfop);
    setFormData({
      codigo: cfop.codigo,
      descricao: cfop.descricao,
      tipo_operacao: cfop.tipo_operacao,
      transferencia: cfop.transferencia,
      ativo: cfop.ativo,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Tem certeza que deseja excluir este CFOP?')) {
      try {
        await adminApi.deleteCFOP(id);
        await loadCfops();
      } catch (error) {
        console.error('Erro ao excluir CFOP:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      codigo: '',
      descricao: '',
      tipo_operacao: 'ENTRADA',
      transferencia: false,
      ativo: true,
    });
    setEditingCfop(null);
    setShowForm(false);
  };

  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Gestão de CFOPs</h1>
        <p className="page-subtitle">Cadastro e configuração de Códigos Fiscais de Operações</p>
      </div>
      
      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">CFOPs Cadastrados</h2>
            <button 
              className="btn btn-primary" 
              onClick={() => setShowForm(true)}
            >
              📋 Novo CFOP
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
                      <th>Código</th>
                      <th>Descrição</th>
                      <th>Tipo Operação</th>
                      <th>Transferência</th>
                      <th>Status</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cfops.map((cfop) => (
                      <tr key={cfop.id}>
                        <td><strong>{cfop.codigo}</strong></td>
                        <td>{cfop.descricao}</td>
                        <td>
                          <span className={`badge ${
                            cfop.tipo_operacao === 'ENTRADA' ? 'badge-info' : 
                            cfop.tipo_operacao === 'SAIDA' ? 'badge-warning' : 'badge-success'
                          }`}>
                            {cfop.tipo_operacao}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${cfop.transferencia ? 'badge-success' : 'badge-secondary'}`}>
                            {cfop.transferencia ? 'Sim' : 'Não'}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${cfop.ativo ? 'badge-success' : 'badge-danger'}`}>
                            {cfop.ativo ? 'Ativo' : 'Inativo'}
                          </span>
                        </td>
                        <td>
                          <button 
                            className="btn btn-sm btn-warning"
                            onClick={() => handleEdit(cfop)}
                          >
                            ✏️
                          </button>
                          <button 
                            className="btn btn-sm btn-danger"
                            onClick={() => handleDelete(cfop.id)}
                            style={{ marginLeft: '8px' }}
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
                {editingCfop ? 'Editar CFOP' : 'Novo CFOP'}
              </h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">Código CFOP *</label>
                      <input
                        type="text"
                        className="form-control"
                        value={formData.codigo}
                        onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
                        placeholder="Ex: 5102, 6102, etc"
                        maxLength={4}
                        required
                      />
                    </div>
                  </div>
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">Tipo de Operação *</label>
                      <select
                        className="form-control"
                        value={formData.tipo_operacao}
                        onChange={(e) => setFormData({ ...formData, tipo_operacao: e.target.value })}
                        required
                      >
                        <option value="ENTRADA">Entrada</option>
                        <option value="SAIDA">Saída</option>
                        <option value="TRANSFERENCIA">Transferência</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Descrição *</label>
                  <textarea
                    className="form-control"
                    value={formData.descricao}
                    onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                    placeholder="Descrição detalhada do CFOP"
                    rows={3}
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">
                        <input
                          type="checkbox"
                          checked={formData.transferencia}
                          onChange={(e) => setFormData({ ...formData, transferencia: e.target.checked })}
                          style={{ marginRight: '8px' }}
                        />
                        Operação de Transferência
                      </label>
                      <small style={{ display: 'block', color: '#666', marginTop: '4px' }}>
                        Marque se este CFOP representa uma transferência entre filiais/estabelecimentos
                      </small>
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
                        CFOP Ativo
                      </label>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-secondary" onClick={resetForm}>
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {editingCfop ? 'Atualizar' : 'Cadastrar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">CFOPs Pré-configurados</h2>
          </div>
          <div className="card-body">
            <div className="alert alert-info">
              <strong>CFOPs de Transferência mais comuns:</strong>
              <ul style={{ marginTop: '10px', marginBottom: '0' }}>
                <li><strong>5152:</strong> Transferência de mercadorias adquiridas ou produzidas pela empresa - Dentro do estado</li>
                <li><strong>6152:</strong> Transferência de mercadorias adquiridas ou produzidas pela empresa - Fora do estado</li>
                <li><strong>5409:</strong> Transferência de produtos acabados produzidos pela empresa - Dentro do estado</li>
                <li><strong>6409:</strong> Transferência de produtos acabados produzidos pela empresa - Fora do estado</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};