import axios from "axios";

// Configuração base da API
const api = axios.create({
  baseURL: "http://localhost:8001/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (config.url?.includes("/certificados") && !config.url?.endsWith("/")) {
    // Adicionar barra final se não tiver
    config.url = config.url.replace(
      /(\/certificados(?:\/[^/]+)?)(?!\?|\/)/,
      "$1/",
    );
  }
  return config;
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 🔍 Log detalhado para erros 422
    if (error.response?.status === 422 && error.response?.data?.detail) {
      console.error(
        "🔍 ERRO 422 - Detail:",
        JSON.stringify(error.response.data.detail, null, 2),
      );

      const msgs = error.response.data.detail.map((err: any) => {
        const field = err.loc?.[err.loc.length - 1] || "campo";
        return `• ${field}: ${err.msg}`;
      });
      console.warn(`⚠️ Campos inválidos:\n${msgs.join("\n")}`);
    }

    console.error("Erro na API:", error);
    return Promise.reject(error);
  },
);

// Tipos da API
export interface NFePublicResponse {
  status: "ok" | "error" | "not_found" | "captcha_required";
  detail?: string;
  chave?: string;
  data?: any;
}

export interface OperacaoPendente {
  id: string;
  tipo: string;
  pasta: string;
  status: string;
  progress: number;
  created_at: string;
}

export interface RelatorioResponse {
  total_xmls: number;
  empresas_cadastradas: number;
  xmls_classificados: number;
  xmls_pendentes: number;
  certificados_validos: number;
  certificados_vencendo: number;
  operacoes_pendentes: OperacaoPendente[];
}

// Funções da API original (mantidas para compatibilidade)
export async function fetchNFe(chave: string): Promise<NFePublicResponse> {
  try {
    const response = await api.get(`/nfe/${chave}`);
    return response.data;
  } catch (error: any) {
    return {
      status: "error",
      detail: error.response?.data?.detail || "Erro na consulta",
    };
  }
}

export async function dfeFetchByChave(
  empresaId: number,
  chave: string,
): Promise<any> {
  try {
    const response = await api.get(`/dfe/${empresaId}/${chave}`);
    return response.data;
  } catch (error: any) {
    return {
      status: "error",
      detail: error.response?.data?.detail || "Erro na consulta DFE",
    };
  }
}

export async function dfeDownloadChaveXml(
  empresaId: number,
  chave: string,
  options: { prefer: string; save: boolean },
): Promise<any> {
  try {
    const response = await api.post(
      `/dfe/${empresaId}/${chave}/download`,
      options,
    );
    return response.data;
  } catch (error: any) {
    return {
      status: "error",
      detail: error.response?.data?.detail || "Erro no download",
    };
  }
}

// Novas funções para o sistema administrativo
export const adminApi = {
  // Dashboard
  async getDashboardStats() {
    const response = await api.get("/dashboard/stats");
    return response.data;
  },

  // Relatório completo
  async getRelatorio() {
    const response = await api.get("/relatorio");
    return response.data;
  },

  // Empresas
  async getEmpresas() {
    const response = await api.get("/empresas");
    return response.data;
  },

  async createEmpresa(data: any) {
    const response = await api.post("/empresas", data);
    return response.data;
  },

  async updateEmpresa(id: number, data: any) {
    const response = await api.put(`/empresas/${id}`, data);
    return response.data;
  },

  async deleteEmpresa(id: number) {
    const response = await api.delete(`/empresas/${id}`);
    return response.data;
  },

  async buscarDiretorios(caminho: string = "/") {
    const response = await api.get(
      `/diretorios?caminho=${encodeURIComponent(caminho)}`,
    );
    return response.data;
  },

  // Certificados
  async getCertificados() {
    const response = await api.get("/certificados");
    return response.data;
  },

  async createCertificado(data: any) {
    const response = await api.post("/certificados/", data);
    return response.data;
  },

  async updateCertificado(id: number, data: any) {
    const response = await api.put(`/certificados/${id}/`, data);
    return response.data;
  },

  async deleteCertificado(id: number) {
    const response = await api.delete(`/certificados/${id}/`);
    return response.data;
  },

  async validateCertificate(arquivo_base64: string, senha: string) {
    const response = await api.post("/certificados/validar/", {
      arquivo_base64,
      senha,
    });
    return response.data;
  },

  // CFOPs
  async getCFOPs() {
    const response = await api.get("/cfops");
    return response.data;
  },

  async createCFOP(data: any) {
    // Enviar objeto JSON com os campos corretos
    const response = await api.post("/cfops", {
      codigo: data.codigo,
      descricao: data.descricao,
      tipo_operacao: data.tipo_operacao,
      ativo: data.ativo,
    });
    return response.data;
  },

  async updateCFOP(id: number, data: any) {
    // Enviar apenas campos editáveis
    const response = await api.put(`/cfops/${id}`, {
      descricao: data.descricao,
      tipo_operacao: data.tipo_operacao,
      ativo: data.ativo,
    });
    return response.data;
  },

  async deleteCFOP(id: number) {
    const response = await api.delete(`/cfops/${id}`);
    return response.data;
  },

  // Classificação
  // async classificarPasta(pasta: string) {
  //   const response = await api.post("/classificar", { pasta });
  //   return response.data;
  // },
  async classificarPasta(
    pasta_origem: string,
    manter_originais: boolean = true,
  ) {
    const response = await api.post("/classificar", {
      pasta_origem,
      manter_originais,
      processar_subdiretorios: true, // opcional
    });
    return response.data;
  },

  async getPendencias() {
    const response = await api.get("/pendencias");
    return response.data;
  },

  async resolverPendencia(id: string, acao: string) {
    const response = await api.post(`/pendencias/${id}/resolver`, { acao });
    return response.data;
  },

  // Upload
  // async uploadFile(file: File) {
  //   const formData = new FormData();
  //   formData.append("file", file);

  //   const response = await api.post("/upload", formData, {
  //     headers: {
  //       "Content-Type": "multipart/form-data",
  //     },
  //   });
  //   return response.data;
  // },
  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append("files", file, file.name); // ← "files" plural!

    const response = await api.post("/upload", formData);
    return response.data;
  },

  // ✅ Se precisar enviar múltiplos arquivos:
  async uploadFiles(files: File[]) {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file, file.name); // ← Mesmo nome, múltiplos valores
    });

    const response = await api.post("/upload", formData);
    return response.data;
  },

  // Logs
  async getLogs(filtros?: any) {
    const params = new URLSearchParams(filtros);
    const response = await api.get(`/logs?${params}`);
    return response.data;
  },

  // XMLs não classificados
  async getXMLsNaoClassificados() {
    const response = await api.get("/xmls/nao-classificados");
    return response.data;
  },

  async classificarXML(xmlId: string, classificacao: string) {
    const response = await api.post(`/xmls/${xmlId}/classificar`, {
      classificacao,
    });
    return response.data;
  },

  // Relatórios
  async getRelatorios(tipo?: string) {
    const params = tipo ? `?tipo=${tipo}` : "";
    const response = await api.get(`/relatorios${params}`);
    return response.data;
  },
};

export default api;
