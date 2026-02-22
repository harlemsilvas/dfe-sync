import axios from 'axios';
// Configuração base da API
const api = axios.create({
    baseURL: 'http://localhost:8001/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});
// Interceptor para tratamento de erros
api.interceptors.response.use((response) => response, (error) => {
    console.error('Erro na API:', error);
    return Promise.reject(error);
});
// Funções da API original (mantidas para compatibilidade)
export async function fetchNFe(chave) {
    try {
        const response = await api.get(`/nfe/${chave}`);
        return response.data;
    }
    catch (error) {
        return {
            status: 'error',
            detail: error.response?.data?.detail || 'Erro na consulta'
        };
    }
}
export async function dfeFetchByChave(empresaId, chave) {
    try {
        const response = await api.get(`/dfe/${empresaId}/${chave}`);
        return response.data;
    }
    catch (error) {
        return {
            status: 'error',
            detail: error.response?.data?.detail || 'Erro na consulta DFE'
        };
    }
}
export async function dfeDownloadChaveXml(empresaId, chave, options) {
    try {
        const response = await api.post(`/dfe/${empresaId}/${chave}/download`, options);
        return response.data;
    }
    catch (error) {
        return {
            status: 'error',
            detail: error.response?.data?.detail || 'Erro no download'
        };
    }
}
// Novas funções para o sistema administrativo
export const adminApi = {
    // Dashboard
    async getDashboardStats() {
        const response = await api.get('/dashboard/stats');
        return response.data;
    },
    // Relatório completo
    async getRelatorio() {
        const response = await api.get('/relatorio');
        return response.data;
    },
    // Empresas
    async getEmpresas() {
        const response = await api.get('/empresas');
        return response.data;
    },
    async createEmpresa(data) {
        const response = await api.post('/empresas', data);
        return response.data;
    },
    async updateEmpresa(id, data) {
        const response = await api.put(`/empresas/${id}`, data);
        return response.data;
    },
    async deleteEmpresa(id) {
        const response = await api.delete(`/empresas/${id}`);
        return response.data;
    },
    async buscarDiretorios(caminho = '/') {
        const response = await api.get(`/diretorios?caminho=${encodeURIComponent(caminho)}`);
        return response.data;
    },
    // Certificados
    async getCertificados() {
        const response = await api.get('/certificados');
        return response.data;
    },
    async createCertificado(data) {
        const response = await api.post('/certificados', data);
        return response.data;
    },
    async updateCertificado(id, data) {
        const response = await api.put(`/certificados/${id}`, data);
        return response.data;
    },
    async deleteCertificado(id) {
        const response = await api.delete(`/certificados/${id}`);
        return response.data;
    },
    // CFOPs
    async getCFOPs() {
        const response = await api.get('/cfops');
        return response.data;
    },
    async createCFOP(data) {
        const response = await api.post('/cfops', data);
        return response.data;
    },
    async updateCFOP(id, data) {
        const response = await api.put(`/cfops/${id}`, data);
        return response.data;
    },
    async deleteCFOP(id) {
        const response = await api.delete(`/cfops/${id}`);
        return response.data;
    },
    // Classificação
    async classificarPasta(pasta) {
        const response = await api.post('/classificar', { pasta });
        return response.data;
    },
    async getPendencias() {
        const response = await api.get('/pendencias');
        return response.data;
    },
    async resolverPendencia(id, acao) {
        const response = await api.post(`/pendencias/${id}/resolver`, { acao });
        return response.data;
    },
    // Upload
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
    // Logs
    async getLogs(filtros) {
        const params = new URLSearchParams(filtros);
        const response = await api.get(`/logs?${params}`);
        return response.data;
    },
    // XMLs não classificados
    async getXMLsNaoClassificados() {
        const response = await api.get('/xmls/nao-classificados');
        return response.data;
    },
    async classificarXML(xmlId, classificacao) {
        const response = await api.post(`/xmls/${xmlId}/classificar`, { classificacao });
        return response.data;
    },
    // Relatórios
    async getRelatorios(tipo) {
        const params = tipo ? `?tipo=${tipo}` : '';
        const response = await api.get(`/relatorios${params}`);
        return response.data;
    },
};
export default api;
