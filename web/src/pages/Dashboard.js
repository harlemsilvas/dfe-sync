import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { adminApi } from '../api/admin';
export const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        loadStats();
    }, []);
    const loadStats = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await adminApi.getDashboardStats();
            setStats(data);
        }
        catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
            setError('Erro ao carregar dados do dashboard');
        }
        finally {
            setLoading(false);
        }
    };
    if (loading) {
        return (_jsxs("div", { className: "loading", children: [_jsx("div", { className: "spinner" }), _jsx("p", { children: "Carregando estat\u00EDsticas..." })] }));
    }
    if (error) {
        return (_jsxs("div", { className: "error-state", children: [_jsx("h2", { children: "\u26A0\uFE0F Erro" }), _jsx("p", { children: error }), _jsx("button", { onClick: loadStats, className: "btn btn-primary", children: "Tentar Novamente" })] }));
    }
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsxs("div", { children: [_jsx("h1", { className: "page-title", children: "Dashboard" }), _jsx("p", { className: "page-subtitle", children: "Vis\u00E3o geral do sistema DFE Sync" }), stats?.ultima_atualizacao && (_jsxs("small", { style: { color: '#666' }, children: ["\u00DAltima atualiza\u00E7\u00E3o: ", new Date(stats.ultima_atualizacao).toLocaleString('pt-BR')] }))] }), _jsx("button", { onClick: loadStats, className: "btn btn-secondary", disabled: loading, children: loading ? '🔄 Atualizando...' : '🔄 Atualizar' })] }), _jsxs("div", { className: "content-body", children: [_jsxs("div", { className: "stats-grid", children: [_jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: stats?.total_xmls || 0 }), _jsx("div", { className: "stat-label", children: "Total de XMLs" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: stats?.empresas_cadastradas || 0 }), _jsx("div", { className: "stat-label", children: "Empresas Cadastradas" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: stats?.xmls_classificados || 0 }), _jsx("div", { className: "stat-label", children: "XMLs Classificados" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: stats?.xmls_pendentes || 0 }), _jsx("div", { className: "stat-label", children: "XMLs Pendentes" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: stats?.certificados_validos || 0 }), _jsx("div", { className: "stat-label", children: "Certificados V\u00E1lidos" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: stats?.certificados_vencendo || 0 }), _jsx("div", { className: "stat-label", children: "Certificados Vencendo" })] })] }), _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "A\u00E7\u00F5es R\u00E1pidas" }) }), _jsx("div", { className: "card-body", children: _jsxs("div", { style: { display: 'flex', gap: '15px', flexWrap: 'wrap' }, children: [_jsx("a", { href: "/importacao", className: "btn btn-primary", children: "\uD83D\uDCC1 Importar XMLs" }), _jsx("a", { href: "/classificacao", className: "btn btn-warning", children: "\uD83D\uDD04 Classificar Pendentes" }), _jsx("a", { href: "/empresas", className: "btn btn-success", children: "\uD83C\uDFE2 Cadastrar Empresa" }), _jsx("a", { href: "/certificados", className: "btn btn-info", children: "\uD83D\uDD10 Gerenciar Certificados" })] }) })] }), _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "Status do Sistema" }) }), _jsxs("div", { className: "card-body", children: [_jsx("div", { className: "alert alert-success", children: "\u2705 Sistema DFE Sync operacional" }), _jsxs("div", { className: "alert alert-info", children: ["\u2139\uFE0F \u00DAltima sincroniza\u00E7\u00E3o: ", new Date().toLocaleString()] }), stats?.certificados_vencendo && stats.certificados_vencendo > 0 && (_jsxs("div", { className: "alert alert-warning", children: ["\u26A0\uFE0F ", stats.certificados_vencendo, " certificado(s) vencendo em breve"] }))] })] })] })] }));
};
