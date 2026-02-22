import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useCallback } from 'react';
import { adminApi } from '../../api/admin';
export const Importacao = () => {
    const [selectedPath, setSelectedPath] = useState('');
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');
    const handlePathSubmit = async (e) => {
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
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Erro ao processar pasta');
        }
        finally {
            setProcessing(false);
        }
    };
    const handleFileUpload = async (e) => {
        const files = e.target.files;
        if (!files || files.length === 0)
            return;
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
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Erro ao fazer upload');
        }
        finally {
            setUploading(false);
        }
    };
    const handleDragOver = useCallback((e) => {
        e.preventDefault();
    }, []);
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files);
        // Simular mudança no input para reaproveitar a lógica
        const input = document.getElementById('file-upload');
        if (input && files.length > 0) {
            const dt = new DataTransfer();
            files.forEach(file => dt.items.add(file));
            input.files = dt.files;
            const event = new Event('change', { bubbles: true });
            input.dispatchEvent(event);
        }
    }, []);
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsx("h1", { className: "page-title", children: "Importa\u00E7\u00E3o de Documentos" }), _jsx("p", { className: "page-subtitle", children: "Importe e processe documentos fiscais automaticamente" })] }), _jsxs("div", { className: "content-body", children: [_jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "\uD83D\uDCC1 Importar de Pasta" }) }), _jsxs("div", { className: "card-body", children: [_jsxs("form", { onSubmit: handlePathSubmit, children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Caminho da Pasta" }), _jsxs("div", { style: { display: 'flex', gap: '10px' }, children: [_jsx("input", { type: "text", className: "form-control", value: selectedPath, onChange: (e) => setSelectedPath(e.target.value), placeholder: "/caminho/para/pasta/com/xmls", style: { flex: 1 } }), _jsx("button", { type: "submit", className: "btn btn-primary", disabled: processing, children: processing ? '⏳ Processando...' : '🚀 Processar' })] })] }), _jsx("small", { style: { color: '#666' }, children: "Informe o caminho completo da pasta contendo arquivos XML ou compactados (ZIP, RAR, 7Z)" })] }), _jsxs("div", { className: "alert alert-info", style: { marginTop: '20px' }, children: [_jsx("strong", { children: "Exemplos de caminhos:" }), _jsxs("ul", { style: { marginTop: '8px', marginBottom: '0' }, children: [_jsx("li", { children: _jsx("code", { children: "/mnt/c/Users/usuario/Desktop/contabilidade/xml" }) }), _jsx("li", { children: _jsx("code", { children: "/home/usuario/documentos/nfe" }) }), _jsx("li", { children: _jsx("code", { children: "/var/data/fiscal/importacao" }) })] })] })] })] }), _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "\uD83D\uDCE4 Upload de Arquivos" }) }), _jsx("div", { className: "card-body", children: _jsxs("div", { className: "upload-area", onDragOver: handleDragOver, onDrop: handleDrop, style: {
                                        border: '2px dashed #ddd',
                                        borderRadius: '8px',
                                        padding: '40px',
                                        textAlign: 'center',
                                        background: '#fafafa',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease'
                                    }, onClick: () => document.getElementById('file-upload')?.click(), children: [_jsx("div", { style: { fontSize: '48px', marginBottom: '20px' }, children: "\uD83D\uDCC1" }), _jsx("h3", { children: "Arraste arquivos aqui ou clique para selecionar" }), _jsx("p", { style: { color: '#666', marginTop: '10px' }, children: "Aceita arquivos XML, ZIP, RAR e 7Z" }), _jsx("input", { id: "file-upload", type: "file", multiple: true, accept: ".xml,.zip,.rar,.7z", onChange: handleFileUpload, style: { display: 'none' }, disabled: uploading }), uploading && (_jsxs("div", { style: { marginTop: '20px' }, children: [_jsx("div", { className: "spinner" }), _jsx("p", { children: "Enviando arquivos..." })] }))] }) })] }), error && (_jsx("div", { className: "card", children: _jsx("div", { className: "card-body", children: _jsxs("div", { className: "alert alert-danger", children: [_jsx("strong", { children: "\u274C Erro:" }), " ", error] }) }) })), results && (_jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "\u2705 Resultados da Importa\u00E7\u00E3o" }) }), _jsx("div", { className: "card-body", children: results.uploads ? (
                                // Resultados de upload
                                _jsxs("div", { children: [_jsxs("div", { className: "alert alert-success", children: [_jsx("strong", { children: "Upload conclu\u00EDdo!" }), " ", results.uploads.length, " arquivo(s) processado(s)"] }), _jsx("div", { className: "table-responsive", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Arquivo" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "XMLs Extra\u00EDdos" }), _jsx("th", { children: "Classifica\u00E7\u00E3o" })] }) }), _jsx("tbody", { children: results.uploads.map((upload, index) => (_jsxs("tr", { children: [_jsx("td", { children: upload.filename }), _jsx("td", { children: _jsx("span", { className: `badge ${upload.success ? 'badge-success' : 'badge-danger'}`, children: upload.success ? 'Sucesso' : 'Erro' }) }), _jsx("td", { children: upload.xmls_count || 0 }), _jsx("td", { children: upload.classification || 'N/A' })] }, index))) })] }) })] })) : (
                                // Resultados de processamento de pasta
                                _jsxs("div", { children: [_jsx("div", { className: "alert alert-success", children: _jsx("strong", { children: "Processamento conclu\u00EDdo!" }) }), _jsxs("div", { className: "stats-grid", children: [_jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: results.arquivos_processados || 0 }), _jsx("div", { className: "stat-label", children: "Arquivos Processados" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: results.xmls_extraidos || 0 }), _jsx("div", { className: "stat-label", children: "XMLs Extra\u00EDdos" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: results.classificados || 0 }), _jsx("div", { className: "stat-label", children: "Classificados" })] }), _jsxs("div", { className: "stat-card", children: [_jsx("div", { className: "stat-number", children: results.pendentes || 0 }), _jsx("div", { className: "stat-label", children: "Pendentes" })] })] }), results.detalhes && results.detalhes.length > 0 && (_jsx("div", { className: "table-responsive", style: { marginTop: '20px' }, children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Arquivo" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "Classifica\u00E7\u00E3o" }), _jsx("th", { children: "Empresa" }), _jsx("th", { children: "Observa\u00E7\u00E3o" })] }) }), _jsx("tbody", { children: results.detalhes.map((detalhe, index) => (_jsxs("tr", { children: [_jsx("td", { children: detalhe.arquivo }), _jsx("td", { children: _jsx("span", { className: `badge ${detalhe.success ? 'badge-success' : 'badge-warning'}`, children: detalhe.status }) }), _jsx("td", { children: detalhe.classificacao }), _jsx("td", { children: detalhe.empresa }), _jsx("td", { children: detalhe.observacao })] }, index))) })] }) }))] })) })] })), _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "\uD83D\uDCD6 Instru\u00E7\u00F5es" }) }), _jsxs("div", { className: "card-body", children: [_jsxs("div", { className: "alert alert-info", children: [_jsx("strong", { children: "Como funciona a importa\u00E7\u00E3o:" }), _jsxs("ol", { style: { marginTop: '10px', marginBottom: '0' }, children: [_jsxs("li", { children: [_jsx("strong", { children: "Extra\u00E7\u00E3o:" }), " Arquivos compactados s\u00E3o extra\u00EDdos automaticamente"] }), _jsxs("li", { children: [_jsx("strong", { children: "Valida\u00E7\u00E3o:" }), " XMLs s\u00E3o validados quanto \u00E0 estrutura e conte\u00FAdo"] }), _jsxs("li", { children: [_jsx("strong", { children: "Classifica\u00E7\u00E3o:" }), " Documentos s\u00E3o classificados conforme regras configuradas"] }), _jsxs("li", { children: [_jsx("strong", { children: "Organiza\u00E7\u00E3o:" }), " Arquivos s\u00E3o organizados na estrutura de pastas"] }), _jsxs("li", { children: [_jsx("strong", { children: "Indexa\u00E7\u00E3o:" }), " Metadados s\u00E3o armazenados no banco de dados"] })] })] }), _jsxs("div", { className: "alert alert-warning", children: [_jsx("strong", { children: "Formatos suportados:" }), _jsxs("ul", { style: { marginTop: '8px', marginBottom: '0' }, children: [_jsxs("li", { children: [_jsx("strong", { children: "XML:" }), " Arquivos individuais de NF-e, CT-e, NFS-e"] }), _jsxs("li", { children: [_jsx("strong", { children: "ZIP:" }), " Arquivos compactados ZIP"] }), _jsxs("li", { children: [_jsx("strong", { children: "RAR:" }), " Arquivos compactados RAR"] }), _jsxs("li", { children: [_jsx("strong", { children: "7Z:" }), " Arquivos compactados 7-Zip"] })] })] })] })] })] })] }));
};
