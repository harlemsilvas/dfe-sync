import React, { useState, useCallback } from 'react';
import { adminApi } from '../../api/admin';

export const Importacao: React.FC = () => {
  const [selectedPath, setSelectedPath] = useState('');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handlePathSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPath.trim()) {
      setError('Selecione uma pasta válida');
      return;
    }

    setProcessing(true);
    setError('');
    setResults(null);

    try {
      const result = await adminApi.classificarPasta(selectedPath);
      setResults(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao processar pasta');
    } finally {
      setProcessing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError('');
    setResults(null);

    try {
      const uploadResults = [];
      for (let i = 0; i < files.length; i++) {
        const result = await adminApi.uploadFile(files[i]);
        uploadResults.push(result);
      }
      setResults({ uploads: uploadResults });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao fazer upload');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    
    // Simular mudança no input para reaproveitar a lógica
    const input = document.getElementById('file-upload') as HTMLInputElement;
    if (input && files.length > 0) {
      const dt = new DataTransfer();
      files.forEach(file => dt.items.add(file));
      input.files = dt.files;
      
      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);
    }
  }, []);

  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Importação de Documentos</h1>
        <p className="page-subtitle">Importe e processe documentos fiscais automaticamente</p>
      </div>
      
      <div className="content-body">
        {/* Importação por Pasta */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📁 Importar de Pasta</h2>
          </div>
          <div className="card-body">
            <form onSubmit={handlePathSubmit}>
              <div className="form-group">
                <label className="form-label">Caminho da Pasta</label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    className="form-control"
                    value={selectedPath}
                    onChange={(e) => setSelectedPath(e.target.value)}
                    placeholder="/caminho/para/pasta/com/xmls"
                    style={{ flex: 1 }}
                  />
                  <button 
                    type="submit" 
                    className="btn btn-primary"
                    disabled={processing}
                  >
                    {processing ? '⏳ Processando...' : '🚀 Processar'}
                  </button>
                </div>
              </div>
              <small style={{ color: '#666' }}>
                Informe o caminho completo da pasta contendo arquivos XML ou compactados (ZIP, RAR, 7Z)
              </small>
            </form>
            
            {/* Exemplos de caminhos */}
            <div className="alert alert-info" style={{ marginTop: '20px' }}>
              <strong>Exemplos de caminhos:</strong>
              <ul style={{ marginTop: '8px', marginBottom: '0' }}>
                <li><code>/mnt/c/Users/usuario/Desktop/contabilidade/xml</code></li>
                <li><code>/home/usuario/documentos/nfe</code></li>
                <li><code>/var/data/fiscal/importacao</code></li>
              </ul>
            </div>
          </div>
        </div>

        {/* Upload de Arquivos */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📤 Upload de Arquivos</h2>
          </div>
          <div className="card-body">
            <div 
              className="upload-area"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              style={{
                border: '2px dashed #ddd',
                borderRadius: '8px',
                padding: '40px',
                textAlign: 'center',
                background: '#fafafa',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
              onClick={() => document.getElementById('file-upload')?.click()}
            >
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📁</div>
              <h3>Arraste arquivos aqui ou clique para selecionar</h3>
              <p style={{ color: '#666', marginTop: '10px' }}>
                Aceita arquivos XML, ZIP, RAR e 7Z
              </p>
              <input
                id="file-upload"
                type="file"
                multiple
                accept=".xml,.zip,.rar,.7z"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                disabled={uploading}
              />
              {uploading && (
                <div style={{ marginTop: '20px' }}>
                  <div className="spinner"></div>
                  <p>Enviando arquivos...</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resultados */}
        {error && (
          <div className="card">
            <div className="card-body">
              <div className="alert alert-danger">
                <strong>❌ Erro:</strong> {error}
              </div>
            </div>
          </div>
        )}

        {results && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">✅ Resultados da Importação</h2>
            </div>
            <div className="card-body">
              {results.uploads ? (
                // Resultados de upload
                <div>
                  <div className="alert alert-success">
                    <strong>Upload concluído!</strong> {results.uploads.length} arquivo(s) processado(s)
                  </div>
                  <div className="table-responsive">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Arquivo</th>
                          <th>Status</th>
                          <th>XMLs Extraídos</th>
                          <th>Classificação</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.uploads.map((upload: any, index: number) => (
                          <tr key={index}>
                            <td>{upload.filename}</td>
                            <td>
                              <span className={`badge ${upload.success ? 'badge-success' : 'badge-danger'}`}>
                                {upload.success ? 'Sucesso' : 'Erro'}
                              </span>
                            </td>
                            <td>{upload.xmls_count || 0}</td>
                            <td>{upload.classification || 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                // Resultados de processamento de pasta
                <div>
                  <div className="alert alert-success">
                    <strong>Processamento concluído!</strong>
                  </div>
                  
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="stat-number">{results.arquivos_processados || 0}</div>
                      <div className="stat-label">Arquivos Processados</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-number">{results.xmls_extraidos || 0}</div>
                      <div className="stat-label">XMLs Extraídos</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-number">{results.classificados || 0}</div>
                      <div className="stat-label">Classificados</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-number">{results.pendentes || 0}</div>
                      <div className="stat-label">Pendentes</div>
                    </div>
                  </div>

                  {results.detalhes && results.detalhes.length > 0 && (
                    <div className="table-responsive" style={{ marginTop: '20px' }}>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Arquivo</th>
                            <th>Status</th>
                            <th>Classificação</th>
                            <th>Empresa</th>
                            <th>Observação</th>
                          </tr>
                        </thead>
                        <tbody>
                          {results.detalhes.map((detalhe: any, index: number) => (
                            <tr key={index}>
                              <td>{detalhe.arquivo}</td>
                              <td>
                                <span className={`badge ${detalhe.success ? 'badge-success' : 'badge-warning'}`}>
                                  {detalhe.status}
                                </span>
                              </td>
                              <td>{detalhe.classificacao}</td>
                              <td>{detalhe.empresa}</td>
                              <td>{detalhe.observacao}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Instruções */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📖 Instruções</h2>
          </div>
          <div className="card-body">
            <div className="alert alert-info">
              <strong>Como funciona a importação:</strong>
              <ol style={{ marginTop: '10px', marginBottom: '0' }}>
                <li><strong>Extração:</strong> Arquivos compactados são extraídos automaticamente</li>
                <li><strong>Validação:</strong> XMLs são validados quanto à estrutura e conteúdo</li>
                <li><strong>Classificação:</strong> Documentos são classificados conforme regras configuradas</li>
                <li><strong>Organização:</strong> Arquivos são organizados na estrutura de pastas</li>
                <li><strong>Indexação:</strong> Metadados são armazenados no banco de dados</li>
              </ol>
            </div>
            
            <div className="alert alert-warning">
              <strong>Formatos suportados:</strong>
              <ul style={{ marginTop: '8px', marginBottom: '0' }}>
                <li><strong>XML:</strong> Arquivos individuais de NF-e, CT-e, NFS-e</li>
                <li><strong>ZIP:</strong> Arquivos compactados ZIP</li>
                <li><strong>RAR:</strong> Arquivos compactados RAR</li>
                <li><strong>7Z:</strong> Arquivos compactados 7-Zip</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};