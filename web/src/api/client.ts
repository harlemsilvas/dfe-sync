export interface NFePublicResponse {
  status: string;
  chave?: string;
  emitente?: any;
  destinatario?: any;
  produtos?: any[];
  eventos?: any[];
  raw_html_hash?: string;
  fetched_at?: string;
  detail?: string;
}

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export async function fetchNFe(chave: string): Promise<NFePublicResponse> {
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
  } catch (e: any) {
    return { status: "error", detail: e.message || String(e) };
  }
}

async function sha256(data: string): Promise<string> {
  const enc = new TextEncoder().encode(data);
  const hash = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// ---- DF-e: consulta autenticada por chave (Distribuição DFe) ----

export interface DFeConsChaveResponseMeta {
  cStat?: string;
  xMotivo?: string;
  ultNSU?: string | null;
  maxNSU?: string | null;
  docs?: { nsu?: string; schema?: string; xml_size?: number }[];
  elapsed?: number;
}

export async function dfeFetchByChave(
  empresaId: number,
  chave: string
): Promise<
  DFeConsChaveResponseMeta & { status: "ok" | "error"; detail?: string }
> {
  const onlyDigits = (chave || "").replace(/\D/g, "");
  if (!onlyDigits || onlyDigits.length !== 44) {
    return { status: "error", detail: "chave_invalida" } as any;
  }
  const url = `${API_BASE}/dfe/conschave?empresa_id=${encodeURIComponent(
    String(empresaId)
  )}&chNFe=${onlyDigits}`;
  try {
    const resp = await fetch(url, { headers: { Accept: "application/json" } });
    if (!resp.ok) {
      return { status: "error", detail: `http_${resp.status}` } as any;
    }
    const json = (await resp.json()) as DFeConsChaveResponseMeta;
    return { status: "ok", ...json } as any;
  } catch (e: any) {
    return { status: "error", detail: e.message || String(e) } as any;
  }
}

export async function dfeDownloadChaveXml(
  empresaId: number,
  chave: string,
  opts?: { prefer?: "procNFe" | "resNFe" | "resEvento"; save?: boolean }
): Promise<{
  status: "ok" | "error";
  xml?: string;
  schema?: string;
  nsu?: string;
  preferred?: string | null;
  saved_path?: string | null;
  detail?: string;
}> {
  const onlyDigits = (chave || "").replace(/\D/g, "");
  if (!onlyDigits || onlyDigits.length !== 44) {
    return { status: "error", detail: "chave_invalida" };
  }
  const params = new URLSearchParams({
    empresa_id: String(empresaId),
    chNFe: onlyDigits,
  });
  if (opts?.prefer) params.set("prefer", opts.prefer);
  if (opts?.save) params.set("save", "true");
  const url = `${API_BASE}/dfe/conschave/download?${params.toString()}`;
  try {
    const resp = await fetch(url, { headers: { Accept: "application/json" } });
    if (!resp.ok) return { status: "error", detail: `http_${resp.status}` };
    const json = await resp.json();
    return json;
  } catch (e: any) {
    return { status: "error", detail: e.message || String(e) };
  }
}
