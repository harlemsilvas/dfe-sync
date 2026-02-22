import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { fetchNFe, dfeFetchByChave, dfeDownloadChaveXml, } from "../api/client";
import { NFeSearchForm } from "../components/NFeSearchForm";
import { ProductsTable } from "../components/ProductsTable";
import { EventsTimeline } from "../components/EventsTimeline";
export const Home = () => {
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [empresaId, setEmpresaId] = useState(1);
    const [dfeKey, setDfeKey] = useState("");
    const [dfeResult, setDfeResult] = useState(null);
    const [dfeError, setDfeError] = useState(null);
    const [prefer, setPrefer] = useState("procNFe");
    const [saveXml, setSaveXml] = useState(false);
    async function onSearch(chave) {
        setLoading(true);
        setError(null);
        setData(null);
        try {
            const resp = await fetchNFe(chave);
            if (resp.status === "error") {
                if (resp.detail === "chave_invalida_curta") {
                    setError("Informe uma chave de 44 dígitos.");
                }
                else if (resp.detail === "invalid_content_type") {
                    setError("Resposta não JSON recebida (possível HTML de captcha ou erro do portal). Tente novamente mais tarde.");
                }
                else if (resp.detail?.startsWith("http_")) {
                    setError(`Erro HTTP ao consultar (${resp.detail.replace("http_", "")} ). Verifique chave e tente novamente.`);
                }
                else {
                    setError(resp.detail || "Erro desconhecido");
                }
            }
            else if (resp.status === "captcha_required") {
                setError("Captcha exigido pelo portal. Tente novamente mais tarde.");
            }
            else if (resp.status === "not_found") {
                setError("Chave não encontrada.");
            }
            else {
                setData(resp);
            }
        }
        catch (e) {
            setError(e.message || String(e));
        }
        finally {
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
        }
        else {
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
    return (_jsxs("div", { style: {
            maxWidth: 960,
            margin: "0 auto",
            padding: 24,
            fontFamily: "system-ui, sans-serif",
        }, children: [_jsx("h1", { children: "Consulta P\u00FAblica NF-e SP" }), _jsx(NFeSearchForm, { onSearch: onSearch, loading: loading }), error && _jsx("div", { style: { color: "red", marginTop: 16 }, children: error }), data && (_jsxs("div", { style: { marginTop: 32 }, children: [_jsx("h2", { children: "Resumo" }), _jsxs("div", { style: {
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))",
                            gap: 12,
                        }, children: [_jsxs("div", { children: [_jsx("h3", { children: "Emitente" }), _jsx("pre", { style: { background: "#f7f7f7", padding: 8 }, children: JSON.stringify(data.emitente, null, 2) })] }), _jsxs("div", { children: [_jsx("h3", { children: "Destinat\u00E1rio" }), _jsx("pre", { style: { background: "#f7f7f7", padding: 8 }, children: JSON.stringify(data.destinatario, null, 2) })] })] }), _jsx("h2", { style: { marginTop: 32 }, children: "Produtos" }), _jsx(ProductsTable, { produtos: data.produtos }), _jsx("h2", { style: { marginTop: 32 }, children: "Eventos" }), _jsx(EventsTimeline, { eventos: data.eventos }), _jsx("h2", { style: { marginTop: 32 }, children: "JSON Bruto" }), _jsx("pre", { style: {
                            background: "#f0f0f0",
                            padding: 12,
                            maxHeight: 400,
                            overflow: "auto",
                        }, children: JSON.stringify(data, null, 2) })] })), _jsx("hr", { style: { margin: "32px 0" } }), _jsx("h1", { children: "Consulta DF-e por Chave (com certificado)" }), _jsxs("div", { style: { display: "flex", gap: 8, alignItems: "center" }, children: [_jsxs("label", { children: ["Empresa ID:", _jsx("input", { type: "number", value: empresaId, onChange: (e) => setEmpresaId(parseInt(e.target.value || "1", 10)), style: { width: 80, marginLeft: 8 } })] }), _jsx("input", { placeholder: "Chave NFe (44 d\u00EDgitos)", value: dfeKey, onChange: (e) => setDfeKey(e.target.value), style: { flex: 1, padding: 8 } }), _jsx("button", { onClick: onSearchDFe, children: "Buscar" }), _jsxs("select", { value: prefer, onChange: (e) => setPrefer(e.target.value), title: "Schema preferido para download", children: [_jsx("option", { value: "procNFe", children: "procNFe" }), _jsx("option", { value: "resNFe", children: "resNFe" }), _jsx("option", { value: "resEvento", children: "resEvento" })] }), _jsxs("label", { style: { display: "flex", gap: 6, alignItems: "center" }, children: [_jsx("input", { type: "checkbox", checked: saveXml, onChange: (e) => setSaveXml(e.target.checked) }), "salvar no storage"] }), _jsx("button", { onClick: onDownloadDFe, children: "Baixar XML" })] }), dfeError && _jsx("div", { style: { color: "red", marginTop: 8 }, children: dfeError }), dfeResult && (_jsxs("div", { style: { marginTop: 16 }, children: [_jsxs("div", { children: [_jsx("strong", { children: "cStat:" }), " ", dfeResult.cStat, " \u2014", " ", _jsx("strong", { children: "xMotivo:" }), " ", dfeResult.xMotivo] }), dfeResult.preferred && (_jsxs("div", { style: { marginTop: 8 }, children: [_jsx("strong", { children: "preferred:" }), " ", dfeResult.preferred] })), dfeResult.saved_path && (_jsxs("div", { style: { marginTop: 8 }, children: [_jsx("strong", { children: "saved_path:" }), " ", dfeResult.saved_path] })), _jsxs("div", { style: { marginTop: 8 }, children: [_jsx("strong", { children: "Documentos:" }), _jsx("pre", { style: { background: "#f7f7f7", padding: 8 }, children: JSON.stringify(dfeResult.docs, null, 2) })] })] }))] }));
};
