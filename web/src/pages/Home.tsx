import React, { useState } from "react";
import {
  fetchNFe,
  NFePublicResponse,
  dfeFetchByChave,
  dfeDownloadChaveXml,
} from "../api/client";
import { NFeSearchForm } from "../components/NFeSearchForm";
import { ProductsTable } from "../components/ProductsTable";
import { EventsTimeline } from "../components/EventsTimeline";

export const Home: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<NFePublicResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [empresaId, setEmpresaId] = useState<number>(1);
  const [dfeKey, setDfeKey] = useState<string>("");
  const [dfeResult, setDfeResult] = useState<any | null>(null);
  const [dfeError, setDfeError] = useState<string | null>(null);
  const [prefer, setPrefer] = useState<"procNFe" | "resNFe" | "resEvento">(
    "procNFe"
  );
  const [saveXml, setSaveXml] = useState<boolean>(false);

  async function onSearch(chave: string) {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const resp = await fetchNFe(chave);
      if (resp.status === "error") {
        if (resp.detail === "chave_invalida_curta") {
          setError("Informe uma chave de 44 dígitos.");
        } else if (resp.detail === "invalid_content_type") {
          setError(
            "Resposta não JSON recebida (possível HTML de captcha ou erro do portal). Tente novamente mais tarde."
          );
        } else if (resp.detail?.startsWith("http_")) {
          setError(
            `Erro HTTP ao consultar (${resp.detail.replace(
              "http_",
              ""
            )} ). Verifique chave e tente novamente.`
          );
        } else {
          setError(resp.detail || "Erro desconhecido");
        }
      } else if (resp.status === "captcha_required") {
        setError("Captcha exigido pelo portal. Tente novamente mais tarde.");
      } else if (resp.status === "not_found") {
        setError("Chave não encontrada.");
      } else {
        setData(resp);
      }
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  async function onSearchDFe() {
    setDfeError(null);
    setDfeResult(null);
    if (!dfeKey || dfeKey.replace(/\D/g, "").length !== 44) {
      setDfeError("Informe uma chave de 44 dígitos.");
      return;
    }
    const meta = await dfeFetchByChave(empresaId, dfeKey);
    if (meta.status === "error") {
      setDfeError(meta.detail || "Erro na consulta DF-e");
    } else {
      setDfeResult(meta);
    }
  }

  async function onDownloadDFe() {
    setDfeError(null);
    if (!dfeKey || dfeKey.replace(/\D/g, "").length !== 44) {
      setDfeError("Informe uma chave de 44 dígitos.");
      return;
    }
    const res = await dfeDownloadChaveXml(empresaId, dfeKey, {
      prefer,
      save: saveXml,
    });
    if (res.status !== "ok") {
      setDfeError(res.detail || "Falha no download do XML");
      return;
    }
    const blob = new Blob([res.xml || ""], {
      type: "application/xml;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${dfeKey}-${res.schema || "dfe"}.xml`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: 24,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1>Consulta Pública NF-e SP</h1>
      <NFeSearchForm onSearch={onSearch} loading={loading} />
      {error && <div style={{ color: "red", marginTop: 16 }}>{error}</div>}
      {data && (
        <div style={{ marginTop: 32 }}>
          <h2>Resumo</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))",
              gap: 12,
            }}
          >
            <div>
              <h3>Emitente</h3>
              <pre style={{ background: "#f7f7f7", padding: 8 }}>
                {JSON.stringify(data.emitente, null, 2)}
              </pre>
            </div>
            <div>
              <h3>Destinatário</h3>
              <pre style={{ background: "#f7f7f7", padding: 8 }}>
                {JSON.stringify(data.destinatario, null, 2)}
              </pre>
            </div>
          </div>
          <h2 style={{ marginTop: 32 }}>Produtos</h2>
          <ProductsTable produtos={data.produtos} />
          <h2 style={{ marginTop: 32 }}>Eventos</h2>
          <EventsTimeline eventos={data.eventos} />
          <h2 style={{ marginTop: 32 }}>JSON Bruto</h2>
          <pre
            style={{
              background: "#f0f0f0",
              padding: 12,
              maxHeight: 400,
              overflow: "auto",
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      <hr style={{ margin: "32px 0" }} />
      <h1>Consulta DF-e por Chave (com certificado)</h1>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <label>
          Empresa ID:
          <input
            type="number"
            value={empresaId}
            onChange={(e) => setEmpresaId(parseInt(e.target.value || "1", 10))}
            style={{ width: 80, marginLeft: 8 }}
          />
        </label>
        <input
          placeholder="Chave NFe (44 dígitos)"
          value={dfeKey}
          onChange={(e) => setDfeKey(e.target.value)}
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={onSearchDFe}>Buscar</button>
        <select
          value={prefer}
          onChange={(e) => setPrefer(e.target.value as any)}
          title="Schema preferido para download"
        >
          <option value="procNFe">procNFe</option>
          <option value="resNFe">resNFe</option>
          <option value="resEvento">resEvento</option>
        </select>
        <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={saveXml}
            onChange={(e) => setSaveXml(e.target.checked)}
          />
          salvar no storage
        </label>
        <button onClick={onDownloadDFe}>Baixar XML</button>
      </div>
      {dfeError && <div style={{ color: "red", marginTop: 8 }}>{dfeError}</div>}
      {dfeResult && (
        <div style={{ marginTop: 16 }}>
          <div>
            <strong>cStat:</strong> {dfeResult.cStat} —{" "}
            <strong>xMotivo:</strong> {dfeResult.xMotivo}
          </div>
          {dfeResult.preferred && (
            <div style={{ marginTop: 8 }}>
              <strong>preferred:</strong> {dfeResult.preferred}
            </div>
          )}
          {dfeResult.saved_path && (
            <div style={{ marginTop: 8 }}>
              <strong>saved_path:</strong> {dfeResult.saved_path}
            </div>
          )}
          <div style={{ marginTop: 8 }}>
            <strong>Documentos:</strong>
            <pre style={{ background: "#f7f7f7", padding: 8 }}>
              {JSON.stringify(dfeResult.docs, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
