import { useState, useEffect } from "react";
import { adminApi } from "../../api/admin";

// Definir tipos TypeScript
interface Certificado {
  id: number;
  empresa_id: number;
  empresa_nome: string;
  empresa_cnpj: string;
  nome_arquivo: string;
  valido_ate: string;
  ativo: boolean;
  created_at: string;
  updated_at: string;
}

interface Empresa {
  id: number;
  cnpj: string;
  razao_social: string;
  nome_fantasia?: string;
  monitorada: boolean;
  ativo: boolean;
}

interface CertificadoFormData {
  empresa_id: string;
  nome_arquivo: string;
  senha: string;
  valido_ate: string;
  ativo: boolean;
  arquivo_base64?: string;
}

export default function Certificados() {
  // Função para parsear datas no formato 'YYYY-MM-DD HH:mm:ss'
  function parseDateString(dateStr: string) {
    if (!dateStr) return null;
    // Substitui espaço por 'T' para formato ISO
    const isoStr = dateStr.replace(" ", "T");
    const date = new Date(isoStr);
    return isNaN(date.getTime()) ? null : date;
  }
  const [certificados, setCertificados] = useState<Certificado[]>([]);
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingCertificado, setEditingCertificado] =
    useState<Certificado | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState<CertificadoFormData>({
    empresa_id: "",
    nome_arquivo: "",
    senha: "",
    valido_ate: "",
    ativo: true,
    arquivo_base64: "",
  });

  const [certificateFile, setCertificateFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<any>(null);

  // Carregar dados iniciais
  useEffect(() => {
    loadCertificados();
    loadEmpresas();
  }, []);

  const loadCertificados = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getCertificados();
      setCertificados(response);
    } catch (error) {
      console.error("Erro ao carregar certificados:", error);
      alert("Erro ao carregar certificados. Verifique a conexão com a API.");
    } finally {
      setLoading(false);
    }
  };

  const loadEmpresas = async () => {
    try {
      const response = await adminApi.getEmpresas();
      setEmpresas(response);
    } catch (error) {
      console.error("Erro ao carregar empresas:", error);
      alert("Erro ao carregar empresas. Verifique a conexão com a API.");
    }
  };

  const resetForm = () => {
    setFormData({
      empresa_id: "",
      nome_arquivo: "",
      senha: "",
      valido_ate: "",
      ativo: true,
      arquivo_base64: "",
    });
    setEditingCertificado(null);
    setShowForm(false);
    setCertificateFile(null);
    setValidationResult(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validações
    if (!formData.empresa_id || !formData.nome_arquivo || !formData.senha) {
      alert("Por favor, preencha todos os campos obrigatórios.");
      return;
    }

    // Se não está editando, precisa do arquivo
    if (!editingCertificado && (!certificateFile || !formData.arquivo_base64)) {
      alert("Por favor, selecione um arquivo de certificado.");
      return;
    }

    // Validar arquivo de certificado
    const validExtensions = [".pfx", ".p12"];
    const fileExtension = formData.nome_arquivo
      .toLowerCase()
      .slice(formData.nome_arquivo.lastIndexOf("."));

    if (!validExtensions.includes(fileExtension)) {
      alert("Arquivo inválido! Use apenas arquivos .pfx ou .p12");
      return;
    }

    try {
      setLoading(true);

      const submitData = {
        empresa_id: parseInt(formData.empresa_id), // ✅ number
        nome_arquivo: formData.nome_arquivo.trim(),
        senha: formData.senha,
        arquivo_base64: formData.arquivo_base64 || undefined, // ✅ undefined
        valido_ate: formData.valido_ate || undefined,
        ativo: !!formData.ativo, // ✅ boolean
      };
      // const submitData = {
      //   ...formData,
      //   empresa_id: parseInt(formData.empresa_id)
      // };
      // 🔍 Debug: ver o que está sendo enviado
      console.log(
        "📤 Payload tipos:",
        Object.fromEntries(
          Object.entries(submitData).map(([k, v]) => [
            k,
            `${typeof v}: ${JSON.stringify(v)}`,
          ]),
        ),
      );

      if (editingCertificado) {
        // Remove arquivo_base64 na edição se não foi alterado
        const { arquivo_base64, ...updateData } = submitData;
        await adminApi.updateCertificado(editingCertificado.id, updateData);
        alert("Certificado atualizado com sucesso!");
      } else {
        await adminApi.createCertificado(submitData);
        alert("Certificado cadastrado com sucesso!");
      }

      resetForm();
      await loadCertificados();
    } catch (error: any) {
      console.error("Erro ao salvar certificado:", error);

      if (error.response?.status === 409) {
        alert("Já existe um certificado ativo para esta empresa.");
      } else if (error.response?.status === 404) {
        alert("Empresa não encontrada.");
      } else if (error.response?.status === 400) {
        alert(
          error.response.data?.detail || "Erro na validação do certificado.",
        );
      } else {
        alert("Erro ao salvar certificado. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (cert: Certificado) => {
    setEditingCertificado(cert);
    setFormData({
      empresa_id: cert.empresa_id.toString(),
      nome_arquivo: cert.nome_arquivo,
      senha: "", // Não preenche a senha por segurança
      valido_ate: cert.valido_ate,
      ativo: cert.ativo,
    });
    setShowForm(true);
  };

  const handleDelete = async (cert: Certificado) => {
    if (
      !window.confirm(
        `Tem certeza que deseja excluir o certificado "${cert.nome_arquivo}" da empresa ${cert.empresa_nome}?`,
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      await adminApi.deleteCertificado(cert.id);
      alert("Certificado excluído com sucesso!");
      await loadCertificados();
    } catch (error: any) {
      console.error("Erro ao excluir certificado:", error);
      alert("Erro ao excluir certificado. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar extensão do arquivo
      const validExtensions = [".pfx", ".p12"];
      const fileExtension = file.name
        .toLowerCase()
        .slice(file.name.lastIndexOf("."));

      if (!validExtensions.includes(fileExtension)) {
        alert("Arquivo inválido! Use apenas arquivos .pfx ou .p12");
        e.target.value = "";
        return;
      }

      // Converter arquivo para base64
      const reader = new FileReader();
      reader.onload = (event) => {
        const base64String = event.target?.result as string;
        setFormData({
          ...formData,
          nome_arquivo: file.name,
          arquivo_base64: base64String,
        });
        setCertificateFile(file);
        setValidationResult(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const validateCertificate = async () => {
    if (!formData.senha || !formData.arquivo_base64) {
      alert("Por favor, selecione um arquivo e digite a senha.");
      return;
    }

    try {
      setLoading(true);
      const result = await adminApi.validateCertificate(
        formData.arquivo_base64,
        formData.senha,
      );
      // const response = await fetch('http://localhost:8001/api/certificados/validar', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({
      //     arquivo_base64: formData.arquivo_base64,
      //     senha: formData.senha
      //   })
      // });

      // const result = await response.json();
      setValidationResult(result);

      if (result.sucesso && result.dados.valido) {
        // Preenche automaticamente a data de validade
        setFormData({
          ...formData,
          valido_ate: result.dados.valido_ate,
        });
        alert("Certificado validado com sucesso!");
      } else {
        alert(
          `Erro na validação: ${result.dados?.erro || result.erro || "Erro desconhecido"}`,
        );
      }
    } catch (error) {
      console.error("Erro ao validar certificado:", error);
      alert("Erro ao validar certificado. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusCertificado = (validoAte: string) => {
    const hoje = new Date();
    const vencimento = new Date(validoAte);
    const diasParaVencer = Math.ceil(
      (vencimento.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (diasParaVencer < 0) {
      return { label: "Vencido", class: "badge-danger" };
    } else if (diasParaVencer <= 30) {
      return { label: "Vencendo", class: "badge-warning" };
    } else {
      return { label: "Válido", class: "badge-success" };
    }
  };

  return (
    <>
      <div className="content-header">
        <h1 className="page-title">Gestão de Certificados</h1>
        <p className="page-subtitle">
          Cadastro e gerenciamento de certificados digitais
        </p>
      </div>

      <div className="content-body">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Certificados Digitais</h2>
            <button
              className="btn btn-primary"
              onClick={() => setShowForm(true)}
              disabled={loading}
            >
              📁 Novo Certificado
            </button>
          </div>

          <div className="card-body">
            {loading && <p>Carregando...</p>}

            {certificados.length === 0 && !loading ? (
              <p className="text-center">Nenhum certificado cadastrado.</p>
            ) : (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Empresa</th>
                      <th>CNPJ</th>
                      <th>Arquivo</th>
                      <th>Válido até</th>
                      <th>Validade</th>
                      <th>Status</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {certificados.map((cert) => {
                      const status = getStatusCertificado(cert.valido_ate);
                      return (
                        <tr key={cert.id}>
                          <td>{cert.id}</td>
                          <td>{cert.empresa_nome}</td>
                          <td>{cert.empresa_cnpj}</td>
                          <td>{cert.nome_arquivo}</td>
                          <td>
                            {(() => {
                              const date = parseDateString(cert.valido_ate);
                              return date
                                ? date.toLocaleDateString("pt-BR")
                                : "—";
                            })()}
                          </td>
                          <td>
                            <span className={`badge ${status.class}`}>
                              {status.label}
                            </span>
                          </td>
                          <td>
                            <span
                              className={`badge ${cert.ativo ? "badge-success" : "badge-danger"}`}
                            >
                              {cert.ativo ? "Ativo" : "Inativo"}
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn btn-sm btn-warning"
                              onClick={() => handleEdit(cert)}
                              title="Editar certificado"
                            >
                              ✏️
                            </button>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleDelete(cert)}
                              style={{ marginLeft: "8px" }}
                              title="Excluir certificado"
                            >
                              🗑️
                            </button>
                          </td>
                        </tr>
                      );
                    })}
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
                {editingCertificado ? "Editar Certificado" : "Novo Certificado"}
              </h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">Empresa *</label>
                      <select
                        value={formData.empresa_id}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            empresa_id: e.target.value,
                          })
                        }
                        className="form-control"
                        required
                      >
                        <option value="">Selecione uma empresa...</option>
                        {empresas.map((empresa) => (
                          <option key={empresa.id} value={empresa.id}>
                            {empresa.razao_social} - CNPJ: {empresa.cnpj}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">
                        Arquivo do Certificado *
                      </label>
                      <input
                        type="file"
                        accept=".pfx,.p12"
                        onChange={handleFileUpload}
                        className="form-control"
                        required={!editingCertificado}
                      />
                      {formData.nome_arquivo && (
                        <small className="form-text">
                          Arquivo selecionado: {formData.nome_arquivo}
                        </small>
                      )}
                    </div>
                  </div>

                  <div className="form-col">
                    <div className="form-group">
                      <label className="form-label">
                        Senha do Certificado *
                      </label>
                      <div className="input-group">
                        <input
                          type="password"
                          value={formData.senha}
                          onChange={(e) =>
                            setFormData({ ...formData, senha: e.target.value })
                          }
                          className="form-control"
                          placeholder="Digite a senha do certificado"
                          required
                        />
                        <button
                          type="button"
                          className="btn btn-outline-primary"
                          onClick={validateCertificate}
                          disabled={
                            loading ||
                            !formData.senha ||
                            !formData.arquivo_base64
                          }
                          style={{ marginLeft: "8px" }}
                        >
                          {loading ? "Validando..." : "🔍 Validar"}
                        </button>
                      </div>
                      {validationResult && (
                        <div
                          className={`alert ${validationResult.sucesso ? "alert-success" : "alert-danger"}`}
                          style={{ marginTop: "8px", padding: "8px" }}
                        >
                          {validationResult.sucesso ? (
                            <div>
                              <strong>✅ Certificado válido!</strong>
                              <br />
                              CN: {validationResult.dados.cn}
                              <br />
                              Válido de: {validationResult.dados.valido_de}
                              <br />
                              Válido até: {validationResult.dados.valido_ate}
                              {validationResult.dados.expirado && (
                                <>
                                  <br />
                                  <span style={{ color: "red" }}>
                                    ⚠️ Certificado expirado
                                  </span>
                                </>
                              )}
                              {validationResult.dados.ainda_nao_valido && (
                                <>
                                  <br />
                                  <span style={{ color: "orange" }}>
                                    ⚠️ Certificado ainda não válido
                                  </span>
                                </>
                              )}
                            </div>
                          ) : (
                            <div>
                              <strong>❌ Erro na validação:</strong>
                              <br />
                              {validationResult.dados?.erro ||
                                validationResult.erro}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="form-group">
                      <label className="form-label">Válido até</label>
                      <input
                        type="text"
                        value={
                          formData.valido_ate
                            ? new Date(formData.valido_ate).toLocaleDateString(
                                "pt-BR",
                              )
                            : ""
                        }
                        className="form-control"
                        placeholder="Será preenchido automaticamente após validação"
                        readOnly
                        style={{ backgroundColor: "#f8f9fa" }}
                      />
                      <small className="form-text">
                        A data de validade será extraída automaticamente do
                        certificado após a validação.
                      </small>
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <div className="form-check">
                    <input
                      type="checkbox"
                      id="ativo"
                      checked={formData.ativo}
                      onChange={(e) =>
                        setFormData({ ...formData, ativo: e.target.checked })
                      }
                      className="form-check-input"
                    />
                    <label htmlFor="ativo" className="form-check-label">
                      Certificado ativo
                    </label>
                  </div>
                </div>

                <div className="form-actions">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading
                      ? "Salvando..."
                      : editingCertificado
                        ? "Atualizar"
                        : "Cadastrar"}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={resetForm}
                    style={{ marginLeft: "8px" }}
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
