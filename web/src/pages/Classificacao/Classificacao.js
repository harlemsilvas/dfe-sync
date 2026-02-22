import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';
export const Classificacao = () => {
    const [xmls, setXmls] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedXmls, setSelectedXmls] = useState(new Set());
    const [showClassifyModal, setShowClassifyModal] = useState(false);
    const [classificacaoSelecionada, setClassificacaoSelecionada] = useState('');
    useEffect(() => {
        loadXmlsNaoClassificados();
    }, []);
    const loadXmlsNaoClassificados = async () => {
        try {
            const data = await adminApi.getXMLsNaoClassificados();
            setXmls(data);
        }
        catch (error) {
            console.error('Erro ao carregar XMLs não classificados:', error);
        }
        finally {
            setLoading(false);
        }
    };
    const handleSelectXml = (xmlId) => {
        const newSelected = new Set(selectedXmls);
        if (newSelected.has(xmlId)) {
            newSelected.delete(xmlId);
        }
        else {
            newSelected.add(xmlId);
        }
        setSelectedXmls(newSelected);
    };
    const handleSelectAll = () => {
        if (selectedXmls.size === xmls.length) {
            setSelectedXmls(new Set());
        }
        else {
            setSelectedXmls(new Set(xmls.map(xml => xml.id)));
        }
    };
    const handleClassificar = async () => {
        if (selectedXmls.size === 0 || !classificacaoSelecionada) {
            alert('Selecione XMLs e uma classificação');
            return;
        }
        try {
            const promises = Array.from(selectedXmls).map(xmlId => adminApi.classificarXML(xmlId, classificacaoSelecionada));
            await Promise.all(promises);
            await loadXmlsNaoClassificados();
            setSelectedXmls(new Set());
            setShowClassifyModal(false);
            setClassificacaoSelecionada('');
        }
        catch (error) {
            console.error('Erro ao classificar XMLs:', error);
        }
    };
    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };
    const formatCNPJ = (cnpj) => {
        return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    };
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsx("h1", { className: "page-title", children: "Classifica\u00E7\u00E3o Manual" }), _jsx("p", { className: "page-subtitle", children: "Classifique documentos fiscais n\u00E3o processados automaticamente" })] }), _jsxs("div", { className: "content-body", children: [_jsxs("div", { className: "card", children: [_jsxs("div", { className: "card-header", children: [_jsxs("h2", { className: "card-title", children: ["XMLs Aguardando Classifica\u00E7\u00E3o (", xmls.length, ")"] }), _jsxs("div", { style: { display: 'flex', gap: '10px' }, children: [selectedXmls.size > 0 && (_jsxs("button", { className: "btn btn-primary", onClick: () => setShowClassifyModal(true), children: ["\uD83D\uDD04 Classificar Selecionados (", selectedXmls.size, ")"] })), _jsx("button", { className: "btn btn-secondary", onClick: loadXmlsNaoClassificados, disabled: loading, children: "\uD83D\uDD04 Atualizar" })] })] }), _jsx("div", { className: "card-body", children: loading ? (_jsx("div", { className: "loading", children: _jsx("div", { className: "spinner" }) })) : xmls.length === 0 ? (_jsx("div", { className: "alert alert-success", children: "\uD83C\uDF89 N\u00E3o h\u00E1 XMLs aguardando classifica\u00E7\u00E3o!" })) : (_jsx("div", { className: "table-responsive", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: _jsx("input", { type: "checkbox", checked: selectedXmls.size === xmls.length, onChange: handleSelectAll }) }), _jsx("th", { children: "Chave de Acesso" }), _jsx("th", { children: "Emitente" }), _jsx("th", { children: "Destinat\u00E1rio" }), _jsx("th", { children: "Valor" }), _jsx("th", { children: "CFOP" }), _jsx("th", { children: "Data Emiss\u00E3o" }), _jsx("th", { children: "Situa\u00E7\u00E3o" }), _jsx("th", { children: "A\u00E7\u00F5es" })] }) }), _jsx("tbody", { children: xmls.map((xml) => (_jsxs("tr", { children: [_jsx("td", { children: _jsx("input", { type: "checkbox", checked: selectedXmls.has(xml.id), onChange: () => handleSelectXml(xml.id) }) }), _jsx("td", { children: _jsx("code", { style: { fontSize: '12px' }, children: xml.chave }) }), _jsx("td", { children: _jsxs("div", { children: [_jsx("strong", { children: xml.emitente_nome }), _jsx("br", {}), _jsx("small", { children: formatCNPJ(xml.emitente_cnpj) })] }) }), _jsx("td", { children: _jsxs("div", { children: [_jsx("strong", { children: xml.destinatario_nome }), _jsx("br", {}), _jsx("small", { children: formatCNPJ(xml.destinatario_cnpj) })] }) }), _jsx("td", { children: formatCurrency(xml.valor_total) }), _jsx("td", { children: _jsx("strong", { children: xml.cfop_principal }) }), _jsx("td", { children: new Date(xml.data_emissao).toLocaleDateString() }), _jsx("td", { children: _jsx("span", { className: "badge badge-warning", children: xml.situacao }) }), _jsx("td", { children: _jsx("a", { href: `/xml-viewer/${xml.id}`, className: "btn btn-sm btn-info", title: "Visualizar XML", children: "\uD83D\uDC41\uFE0F" }) })] }, xml.id))) })] }) })) })] }), showClassifyModal && (_jsx("div", { className: "modal-overlay", onClick: () => setShowClassifyModal(false), children: _jsx("div", { className: "modal-content", onClick: (e) => e.stopPropagation(), children: _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "Classificar XMLs Selecionados" }) }), _jsxs("div", { className: "card-body", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Classifica\u00E7\u00E3o" }), _jsxs("select", { className: "form-control", value: classificacaoSelecionada, onChange: (e) => setClassificacaoSelecionada(e.target.value), children: [_jsx("option", { value: "", children: "Selecione uma classifica\u00E7\u00E3o" }), _jsx("option", { value: "NFE_ENTRADA", children: "NF-e Entrada" }), _jsx("option", { value: "NFE_SAIDA", children: "NF-e Sa\u00EDda" }), _jsx("option", { value: "NFE_TRANSFERENCIA", children: "NF-e Transfer\u00EAncia" }), _jsx("option", { value: "NFE_TERCEIROS", children: "NF-e Terceiros" }), _jsx("option", { value: "CTE", children: "CT-e" }), _jsx("option", { value: "NFSE", children: "NFS-e" }), _jsx("option", { value: "EVENTO", children: "Evento" })] })] }), _jsxs("div", { className: "alert alert-info", children: [_jsx("strong", { children: "XMLs selecionados:" }), " ", selectedXmls.size, _jsx("br", {}), "Esta a\u00E7\u00E3o ir\u00E1 classificar todos os XMLs selecionados com a mesma classifica\u00E7\u00E3o."] }), _jsxs("div", { style: { display: 'flex', gap: '10px', justifyContent: 'flex-end' }, children: [_jsx("button", { className: "btn btn-secondary", onClick: () => setShowClassifyModal(false), children: "Cancelar" }), _jsx("button", { className: "btn btn-primary", onClick: handleClassificar, disabled: !classificacaoSelecionada, children: "Classificar" })] })] })] }) }) })), _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "\uD83D\uDCCB Regras de Classifica\u00E7\u00E3o" }) }), _jsx("div", { className: "card-body", children: _jsxs("div", { className: "alert alert-info", children: [_jsx("strong", { children: "Tipos de Classifica\u00E7\u00E3o:" }), _jsxs("ul", { style: { marginTop: '10px', marginBottom: '0' }, children: [_jsxs("li", { children: [_jsx("strong", { children: "NF-e Entrada:" }), " CNPJ destinat\u00E1rio \u00E9 empresa monitorada"] }), _jsxs("li", { children: [_jsx("strong", { children: "NF-e Sa\u00EDda:" }), " CNPJ emitente \u00E9 empresa monitorada"] }), _jsxs("li", { children: [_jsx("strong", { children: "NF-e Transfer\u00EAncia:" }), " CFOPs de transfer\u00EAncia (5152, 6152, 5409, 6409)"] }), _jsxs("li", { children: [_jsx("strong", { children: "NF-e Terceiros:" }), " Nenhum CNPJ \u00E9 empresa monitorada"] }), _jsxs("li", { children: [_jsx("strong", { children: "CT-e:" }), " Conhecimento de Transporte (modelo 57)"] }), _jsxs("li", { children: [_jsx("strong", { children: "NFS-e:" }), " Nota Fiscal de Servi\u00E7os"] }), _jsxs("li", { children: [_jsx("strong", { children: "Evento:" }), " Eventos relacionados (cancelamento, corre\u00E7\u00E3o, etc.)"] })] })] }) })] })] }), _jsx("style", { jsx: true, children: `
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
      ` })] }));
};
