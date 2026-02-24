import React, { useState, useEffect } from "react";
import { adminApi } from "../../api/admin";

interface XMLNaoClassificado {
  arquivo: string;
  status: string;
  tamanho: number;
  // Campos opcionais que podem não existir na API atual
  id?: string;
  chave?: string;
  emitente_cnpj?: string;
  emitente_nome?: string;
  destinatario_cnpj?: string;
  destinatario_nome?: string;
  valor_total?: number;
  data_emissao?: string;
  cfop_principal?: string;
  situacao?: string;
}

export const Classificacao: React.FC = () => {
  const [xmls, setXmls] = useState<XMLNaoClassificado[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedXmls, setSelectedXmls] = useState<Set<string>>(new Set());
  const [showClassifyModal, setShowClassifyModal] = useState(false);
  const [classificacaoSelecionada, setClassificacaoSelecionada] =
    useState("AUTO");
  const [progress, setProgress] = useState(0);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [summary, setSummary] = useState<{
    total: number;
    sucesso: number;
    erro: number;
    tipos: Record<string, number>;
  }>({ total: 0, sucesso: 0, erro: 0, tipos: {} });

  useEffect(() => {
    loadXmlsNaoClassificados();
  }, []);

  const loadXmlsNaoClassificados = async () => {
    try {
      const data = await adminApi.getXMLsNaoClassificados();
      // A API retorna um objeto com { total, xmls }, então precisamos acessar xmls
      const xmlsList = data?.xmls || [];
      setXmls(Array.isArray(xmlsList) ? xmlsList : []);
    } catch (error) {
      console.error("Erro ao carregar XMLs não classificados:", error);
      setXmls([]); // Garantir que xmls seja sempre um array
    } finally {
      setLoading(false);
    }
  };

  const handleSelectXml = (xmlArquivo: string) => {
    const newSelected = new Set(selectedXmls);
    if (newSelected.has(xmlArquivo)) {
      newSelected.delete(xmlArquivo);
    } else {
      newSelected.add(xmlArquivo);
    }
    setSelectedXmls(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedXmls.size === xmls.length) {
      setSelectedXmls(new Set());
    } else {
      setSelectedXmls(new Set(xmls.map((xml) => xml.arquivo)));
    }
  };

  const handleClassificar = async () => {
    if (selectedXmls.size === 0) {
      alert("Selecione XMLs para classificar");
      return;
    }

    setProgress(0);
    setShowClassifyModal(false);
    setShowSummaryModal(true);
    const total = selectedXmls.size;
    let sucesso = 0;
    let erro = 0;
    const tipos: Record<string, number> = {};
    let idx = 0;
    for (const xmlId of selectedXmls) {
      try {
        let result;
        if (classificacaoSelecionada === "AUTO") {
          result = await adminApi.classificarXML(xmlId);
        } else {
          result = await adminApi.classificarXML(
            xmlId,
            classificacaoSelecionada,
          );
        }
        if (result && result.metadados && !result.metadados.erro_parsing) {
          sucesso++;
          const tipo = result.metadados.tipo_documento || "Desconhecido";
          tipos[tipo] = (tipos[tipo] || 0) + 1;
        } else {
          erro++;
        }
      } catch {
        erro++;
      }
      idx++;
      setProgress(Math.round((idx / total) * 100));
    }
    setSummary({ total, sucesso, erro, tipos });
    await loadXmlsNaoClassificados();
    setSelectedXmls(new Set());
    setClassificacaoSelecionada("AUTO");
    setTimeout(() => setShowSummaryModal(false), 3000);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  const formatCNPJ = (cnpj: string) => {
    return cnpj.replace(
      /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
      "$1.$2.$3/$4-$5",
    );
  };

  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Classificação Manual</h1>
        <p className="page-subtitle">
          Classifique documentos fiscais não processados automaticamente
        </p>
      </div>

      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              XMLs Aguardando Classificação ({xmls.length})
            </h2>
            <div style={{ display: "flex", gap: "10px" }}>
              {selectedXmls.size > 0 && (
                <button
                  className="btn btn-primary"
                  onClick={() => setShowClassifyModal(true)}
                >
                  🔄 Classificar Selecionados ({selectedXmls.size})
                </button>
              )}
              <button
                className="btn btn-secondary"
                onClick={loadXmlsNaoClassificados}
                disabled={loading}
              >
                🔄 Atualizar
              </button>
            </div>
          </div>

          <div className="card-body">
            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
              </div>
            ) : xmls.length === 0 ? (
              <div className="alert alert-success">
                🎉 Não há XMLs aguardando classificação!
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>
                        <input
                          type="checkbox"
                          checked={selectedXmls.size === xmls.length}
                          onChange={handleSelectAll}
                        />
                      </th>
                      <th>Chave de Acesso</th>
                      <th>Emitente</th>
                      <th>Destinatário</th>
                      <th>Valor</th>
                      <th>CFOP</th>
                      <th>Data Emissão</th>
                      <th>Situação</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.isArray(xmls) &&
                      xmls.map((xml) => (
                        <tr key={xml.arquivo}>
                          <td>
                            <input
                              type="checkbox"
                              checked={selectedXmls.has(xml.arquivo)}
                              onChange={() => handleSelectXml(xml.arquivo)}
                            />
                          </td>
                          <td>
                            <code style={{ fontSize: "12px" }}>
                              {xml.chave || xml.arquivo.split("-")[0] || "N/A"}
                            </code>
                          </td>
                          <td>
                            <div>
                              <strong>
                                {xml.emitente_nome || "Não informado"}
                              </strong>
                              <br />
                              <small>
                                {xml.emitente_cnpj
                                  ? formatCNPJ(xml.emitente_cnpj)
                                  : "N/A"}
                              </small>
                            </div>
                          </td>
                          <td>
                            <div>
                              <strong>
                                {xml.destinatario_nome || "Não informado"}
                              </strong>
                              <br />
                              <small>
                                {xml.destinatario_cnpj
                                  ? formatCNPJ(xml.destinatario_cnpj)
                                  : "N/A"}
                              </small>
                            </div>
                          </td>
                          <td>
                            {xml.valor_total
                              ? formatCurrency(xml.valor_total)
                              : "N/A"}
                          </td>
                          <td>
                            <strong>{xml.cfop_principal || "N/A"}</strong>
                          </td>
                          <td>
                            {xml.data_emissao
                              ? new Date(xml.data_emissao).toLocaleDateString()
                              : "N/A"}
                          </td>
                          <td>
                            <span
                              className={`badge ${xml.status === "pendente" ? "badge-warning" : "badge-info"}`}
                            >
                              {xml.situacao || xml.status || "Pendente"}
                            </span>
                          </td>
                          <td>
                            <a
                              href={`/xml-viewer/${encodeURIComponent(xml.arquivo)}`}
                              className="btn btn-sm btn-info"
                              title="Visualizar XML"
                            >
                              👁️
                            </a>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Modal de Resumo da Classificação */}
        {showSummaryModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title">Resumo da Classificação</h2>
                </div>
                <div className="card-body">
                  <div style={{ marginBottom: 20 }}>
                    <div
                      className="progress-bar"
                      style={{
                        width: "100%",
                        background: "#eee",
                        height: 10,
                        borderRadius: 5,
                      }}
                    >
                      <div
                        style={{
                          width: `${progress}%`,
                          background: "#007bff",
                          height: 10,
                          borderRadius: 5,
                          transition: "width 0.3s",
                        }}
                      ></div>
                    </div>
                    <div style={{ marginTop: 8, fontSize: 14 }}>
                      {progress}% concluído
                    </div>
                  </div>
                  <div>
                    <strong>Total:</strong> {summary.total}
                    <br />
                    <strong>Sucesso:</strong> {summary.sucesso}
                    <br />
                    <strong>Erro:</strong> {summary.erro}
                    <br />
                    <strong>Tipos:</strong>
                    <ul>
                      {Object.entries(summary.tipos).map(([tipo, qtd]) => (
                        <li key={tipo}>
                          {tipo}: {qtd}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div style={{ marginTop: 10, color: "#888" }}>
                    Fechando em alguns segundos...
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Classificação */}
        {showClassifyModal && (
          <div
            className="modal-overlay"
            onClick={() => setShowClassifyModal(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title">Classificar XMLs Selecionados</h2>
                </div>
                <div className="card-body">
                  <div className="form-group">
                    <label className="form-label">Classificação</label>
                    <select
                      className="form-control"
                      value={classificacaoSelecionada}
                      onChange={(e) =>
                        setClassificacaoSelecionada(e.target.value)
                      }
                    >
                      <option value="AUTO">Auto-Classificar (padrão)</option>
                      <option value="NFE_ENTRADA">NF-e Entrada</option>
                      <option value="NFE_SAIDA">NF-e Saída</option>
                      <option value="NFE_TRANSFERENCIA">
                        NF-e Transferência
                      </option>
                      <option value="NFE_TERCEIROS">NF-e Terceiros</option>
                      <option value="CTE">CT-e</option>
                      <option value="NFSE">NFS-e</option>
                      <option value="EVENTO">Evento</option>
                    </select>
                  </div>

                  <div className="alert alert-info">
                    <strong>XMLs selecionados:</strong> {selectedXmls.size}
                    <br />
                    Esta ação irá classificar todos os XMLs selecionados com a
                    mesma classificação.
                  </div>

                  <div
                    style={{
                      display: "flex",
                      gap: "10px",
                      justifyContent: "flex-end",
                    }}
                  >
                    <button
                      className="btn btn-secondary"
                      onClick={() => setShowClassifyModal(false)}
                    >
                      Cancelar
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleClassificar}
                      disabled={!classificacaoSelecionada}
                    >
                      Classificar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Instruções */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📋 Regras de Classificação</h2>
          </div>
          <div className="card-body">
            <div className="alert alert-info">
              <strong>Tipos de Classificação:</strong>
              <ul style={{ marginTop: "10px", marginBottom: "0" }}>
                <li>
                  <strong>NF-e Entrada:</strong> CNPJ destinatário é empresa
                  monitorada
                </li>
                <li>
                  <strong>NF-e Saída:</strong> CNPJ emitente é empresa
                  monitorada
                </li>
                <li>
                  <strong>NF-e Transferência:</strong> CFOPs de transferência
                  (5152, 6152, 5409, 6409)
                </li>
                <li>
                  <strong>NF-e Terceiros:</strong> Nenhum CNPJ é empresa
                  monitorada
                </li>
                <li>
                  <strong>CT-e:</strong> Conhecimento de Transporte (modelo 57)
                </li>
                <li>
                  <strong>NFS-e:</strong> Nota Fiscal de Serviços
                </li>
                <li>
                  <strong>Evento:</strong> Eventos relacionados (cancelamento,
                  correção, etc.)
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          max-width: 500px;
          width: 90%;
          max-height: 90%;
          overflow: auto;
        }
      `}</style>
    </>
  );
};
