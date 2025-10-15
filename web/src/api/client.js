const API_BASE = import.meta.env.VITE_API_BASE || "/api";
export async function fetchNFe(chave) {
    // Interceptor simples: ignorar requisições com chave vazia ou tamanho != 44
    const onlyDigits = (chave || "").replace(/\D/g, "");
    if (!onlyDigits || onlyDigits.length < 44) {
        return { status: "error", detail: "chave_invalida_curta" };
    }
    const url = `${API_BASE}/nfe/sp/publica/${onlyDigits}`;
    try {
        const resp = await fetch(url, { headers: { Accept: "application/json" } });
        const contentType = resp.headers.get("content-type") || "";
        if (!resp.ok) {
            // tentar extrair texto para diagnosticar
            const txt = await resp.text().catch(() => "");
            return {
                status: "error",
                detail: `http_${resp.status}`,
                raw_html_hash: txt ? `sha256:${await sha256(txt)}` : undefined,
            };
        }
        if (!contentType.includes("application/json")) {
            const txt = await resp.text();
            return {
                status: "error",
                detail: "invalid_content_type",
                raw_html_hash: `sha256:${await sha256(txt)}`,
            };
        }
        return await resp.json();
    }
    catch (e) {
        return { status: "error", detail: e.message || String(e) };
    }
}
async function sha256(data) {
    const enc = new TextEncoder().encode(data);
    const hash = await crypto.subtle.digest("SHA-256", enc);
    return Array.from(new Uint8Array(hash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}
export async function dfeFetchByChave(empresaId, chave) {
    const onlyDigits = (chave || "").replace(/\D/g, "");
    if (!onlyDigits || onlyDigits.length !== 44) {
        return { status: "error", detail: "chave_invalida" };
    }
    const url = `${API_BASE}/dfe/conschave?empresa_id=${encodeURIComponent(String(empresaId))}&chNFe=${onlyDigits}`;
    try {
        const resp = await fetch(url, { headers: { Accept: "application/json" } });
        if (!resp.ok) {
            return { status: "error", detail: `http_${resp.status}` };
        }
        const json = (await resp.json());
        return { status: "ok", ...json };
    }
    catch (e) {
        return { status: "error", detail: e.message || String(e) };
    }
}
export async function dfeDownloadChaveXml(empresaId, chave, opts) {
    const onlyDigits = (chave || "").replace(/\D/g, "");
    if (!onlyDigits || onlyDigits.length !== 44) {
        return { status: "error", detail: "chave_invalida" };
    }
    const params = new URLSearchParams({
        empresa_id: String(empresaId),
        chNFe: onlyDigits,
    });
    if (opts?.prefer)
        params.set("prefer", opts.prefer);
    if (opts?.save)
        params.set("save", "true");
    const url = `${API_BASE}/dfe/conschave/download?${params.toString()}`;
    try {
        const resp = await fetch(url, { headers: { Accept: "application/json" } });
        if (!resp.ok)
            return { status: "error", detail: `http_${resp.status}` };
        const json = await resp.json();
        return json;
    }
    catch (e) {
        return { status: "error", detail: e.message || String(e) };
    }
}
