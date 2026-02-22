import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';
export const CFOPs = () => {
    const [cfops, setCfops] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingCfop, setEditingCfop] = useState(null);
    const [formData, setFormData] = useState({
        codigo: '',
        descricao: '',
        tipo_operacao: 'ENTRADA',
        transferencia: false,
        ativo: true,
    });
    useEffect(() => {
        loadCfops();
    }, []);
    const loadCfops = async () => {
        try {
            const data = await adminApi.getCFOPs();
            setCfops(data);
        }
        catch (error) {
            console.error('Erro ao carregar CFOPs:', error);
        }
        finally {
            setLoading(false);
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingCfop) {
                await adminApi.updateCFOP(editingCfop.id, formData);
            }
            else {
                await adminApi.createCFOP(formData);
            }
            await loadCfops();
            resetForm();
        }
        catch (error) {
            console.error('Erro ao salvar CFOP:', error);
        }
    };
    const handleEdit = (cfop) => {
        setEditingCfop(cfop);
        setFormData({
            codigo: cfop.codigo,
            descricao: cfop.descricao,
            tipo_operacao: cfop.tipo_operacao,
            transferencia: cfop.transferencia,
            ativo: cfop.ativo,
        });
        setShowForm(true);
    };
    const handleDelete = async (id) => {
        if (confirm('Tem certeza que deseja excluir este CFOP?')) {
            try {
                await adminApi.deleteCFOP(id);
                await loadCfops();
            }
            catch (error) {
                console.error('Erro ao excluir CFOP:', error);
            }
        }
    };
    const resetForm = () => {
        setFormData({
            codigo: '',
            descricao: '',
            tipo_operacao: 'ENTRADA',
            transferencia: false,
            ativo: true,
        });
        setEditingCfop(null);
        setShowForm(false);
    };
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsx("h1", { className: "page-title", children: "Gest\u00E3o de CFOPs" }), _jsx("p", { className: "page-subtitle", children: "Cadastro e configura\u00E7\u00E3o de C\u00F3digos Fiscais de Opera\u00E7\u00F5es" })] }), _jsxs("div", { className: "content-body", children: [_jsxs("div", { className: "card", children: [_jsxs("div", { className: "card-header", children: [_jsx("h2", { className: "card-title", children: "CFOPs Cadastrados" }), _jsx("button", { className: "btn btn-primary", onClick: () => setShowForm(true), children: "\uD83D\uDCCB Novo CFOP" })] }), _jsx("div", { className: "card-body", children: loading ? (_jsx("div", { className: "loading", children: _jsx("div", { className: "spinner" }) })) : (_jsx("div", { className: "table-responsive", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "C\u00F3digo" }), _jsx("th", { children: "Descri\u00E7\u00E3o" }), _jsx("th", { children: "Tipo Opera\u00E7\u00E3o" }), _jsx("th", { children: "Transfer\u00EAncia" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "A\u00E7\u00F5es" })] }) }), _jsx("tbody", { children: cfops.map((cfop) => (_jsxs("tr", { children: [_jsx("td", { children: _jsx("strong", { children: cfop.codigo }) }), _jsx("td", { children: cfop.descricao }), _jsx("td", { children: _jsx("span", { className: `badge ${cfop.tipo_operacao === 'ENTRADA' ? 'badge-info' :
                                                                    cfop.tipo_operacao === 'SAIDA' ? 'badge-warning' : 'badge-success'}`, children: cfop.tipo_operacao }) }), _jsx("td", { children: _jsx("span", { className: `badge ${cfop.transferencia ? 'badge-success' : 'badge-secondary'}`, children: cfop.transferencia ? 'Sim' : 'Não' }) }), _jsx("td", { children: _jsx("span", { className: `badge ${cfop.ativo ? 'badge-success' : 'badge-danger'}`, children: cfop.ativo ? 'Ativo' : 'Inativo' }) }), _jsxs("td", { children: [_jsx("button", { className: "btn btn-sm btn-warning", onClick: () => handleEdit(cfop), children: "\u270F\uFE0F" }), _jsx("button", { className: "btn btn-sm btn-danger", onClick: () => handleDelete(cfop.id), style: { marginLeft: '8px' }, children: "\uD83D\uDDD1\uFE0F" })] })] }, cfop.id))) })] }) })) })] }), showForm && (_jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: editingCfop ? 'Editar CFOP' : 'Novo CFOP' }) }), _jsx("div", { className: "card-body", children: _jsxs("form", { onSubmit: handleSubmit, children: [_jsxs("div", { className: "form-row", children: [_jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "C\u00F3digo CFOP *" }), _jsx("input", { type: "text", className: "form-control", value: formData.codigo, onChange: (e) => setFormData({ ...formData, codigo: e.target.value }), placeholder: "Ex: 5102, 6102, etc", maxLength: 4, required: true })] }) }), _jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Tipo de Opera\u00E7\u00E3o *" }), _jsxs("select", { className: "form-control", value: formData.tipo_operacao, onChange: (e) => setFormData({ ...formData, tipo_operacao: e.target.value }), required: true, children: [_jsx("option", { value: "ENTRADA", children: "Entrada" }), _jsx("option", { value: "SAIDA", children: "Sa\u00EDda" }), _jsx("option", { value: "TRANSFERENCIA", children: "Transfer\u00EAncia" })] })] }) })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Descri\u00E7\u00E3o *" }), _jsx("textarea", { className: "form-control", value: formData.descricao, onChange: (e) => setFormData({ ...formData, descricao: e.target.value }), placeholder: "Descri\u00E7\u00E3o detalhada do CFOP", rows: 3, required: true })] }), _jsxs("div", { className: "form-row", children: [_jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsxs("label", { className: "form-label", children: [_jsx("input", { type: "checkbox", checked: formData.transferencia, onChange: (e) => setFormData({ ...formData, transferencia: e.target.checked }), style: { marginRight: '8px' } }), "Opera\u00E7\u00E3o de Transfer\u00EAncia"] }), _jsx("small", { style: { display: 'block', color: '#666', marginTop: '4px' }, children: "Marque se este CFOP representa uma transfer\u00EAncia entre filiais/estabelecimentos" })] }) }), _jsx("div", { className: "form-col", children: _jsx("div", { className: "form-group", children: _jsxs("label", { className: "form-label", children: [_jsx("input", { type: "checkbox", checked: formData.ativo, onChange: (e) => setFormData({ ...formData, ativo: e.target.checked }), style: { marginRight: '8px' } }), "CFOP Ativo"] }) }) })] }), _jsxs("div", { style: { display: 'flex', gap: '10px', justifyContent: 'flex-end' }, children: [_jsx("button", { type: "button", className: "btn btn-secondary", onClick: resetForm, children: "Cancelar" }), _jsx("button", { type: "submit", className: "btn btn-primary", children: editingCfop ? 'Atualizar' : 'Cadastrar' })] })] }) })] })), _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: "CFOPs Pr\u00E9-configurados" }) }), _jsx("div", { className: "card-body", children: _jsxs("div", { className: "alert alert-info", children: [_jsx("strong", { children: "CFOPs de Transfer\u00EAncia mais comuns:" }), _jsxs("ul", { style: { marginTop: '10px', marginBottom: '0' }, children: [_jsxs("li", { children: [_jsx("strong", { children: "5152:" }), " Transfer\u00EAncia de mercadorias adquiridas ou produzidas pela empresa - Dentro do estado"] }), _jsxs("li", { children: [_jsx("strong", { children: "6152:" }), " Transfer\u00EAncia de mercadorias adquiridas ou produzidas pela empresa - Fora do estado"] }), _jsxs("li", { children: [_jsx("strong", { children: "5409:" }), " Transfer\u00EAncia de produtos acabados produzidos pela empresa - Dentro do estado"] }), _jsxs("li", { children: [_jsx("strong", { children: "6409:" }), " Transfer\u00EAncia de produtos acabados produzidos pela empresa - Fora do estado"] })] })] }) })] })] })] }));
};
