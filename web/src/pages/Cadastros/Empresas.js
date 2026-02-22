import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';
export const Empresas = () => {
    const [empresas, setEmpresas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingEmpresa, setEditingEmpresa] = useState(null);
    const [showDirBrowser, setShowDirBrowser] = useState(false);
    const [currentPath, setCurrentPath] = useState('/');
    const [directorios, setDirectorios] = useState([]);
    const [loadingDir, setLoadingDir] = useState(false);
    const [formData, setFormData] = useState({
        cnpj: '',
        razao_social: '',
        nome_fantasia: '',
        monitorada: true,
        pasta_origem: '',
        ativo: true,
    });
    useEffect(() => {
        loadEmpresas();
    }, []);
    const loadEmpresas = async () => {
        try {
            const data = await adminApi.getEmpresas();
            setEmpresas(data);
        }
        catch (error) {
            console.error('Erro ao carregar empresas:', error);
        }
        finally {
            setLoading(false);
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingEmpresa) {
                await adminApi.updateEmpresa(editingEmpresa.id, formData);
            }
            else {
                await adminApi.createEmpresa(formData);
            }
            await loadEmpresas();
            resetForm();
        }
        catch (error) {
            console.error('Erro ao salvar empresa:', error);
        }
    };
    const handleEdit = (empresa) => {
        setEditingEmpresa(empresa);
        setFormData({
            cnpj: empresa.cnpj,
            razao_social: empresa.razao_social,
            nome_fantasia: empresa.nome_fantasia || '',
            monitorada: empresa.monitorada,
            pasta_origem: empresa.pasta_origem || '',
            ativo: empresa.ativo,
        });
        setShowForm(true);
    };
    const handleDelete = async (id) => {
        if (confirm('Tem certeza que deseja excluir esta empresa?')) {
            try {
                await adminApi.deleteEmpresa(id);
                await loadEmpresas();
            }
            catch (error) {
                console.error('Erro ao excluir empresa:', error);
            }
        }
    };
    const resetForm = () => {
        setFormData({
            cnpj: '',
            razao_social: '',
            nome_fantasia: '',
            monitorada: true,
            pasta_origem: '',
            ativo: true,
        });
        setEditingEmpresa(null);
        setShowForm(false);
    };
    const formatCNPJ = (cnpj) => {
        return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    };
    const loadDirectorios = async (caminho = '/') => {
        setLoadingDir(true);
        try {
            const response = await adminApi.buscarDiretorios(caminho);
            setDirectorios(response.diretorios || []);
            setCurrentPath(response.caminho_atual);
        }
        catch (error) {
            console.error('Erro ao carregar diretórios:', error);
            alert('Erro ao carregar diretórios');
        }
        finally {
            setLoadingDir(false);
        }
    };
    const handleSelectDirectory = (dir) => {
        if (dir.tipo === 'diretorio' || dir.tipo === 'voltar') {
            loadDirectorios(dir.caminho);
        }
    };
    const handleUseDirectory = () => {
        setFormData({ ...formData, pasta_origem: currentPath });
        setShowDirBrowser(false);
    };
    const handleDeleteEmpresa = async (empresa) => {
        if (!confirm(`Deseja realmente excluir a empresa ${empresa.razao_social}?`)) {
            return;
        }
        try {
            await adminApi.deleteEmpresa(empresa.id);
            alert('Empresa excluída com sucesso!');
            loadEmpresas();
        }
        catch (error) {
            console.error('Erro ao excluir empresa:', error);
            alert('Erro ao excluir empresa');
        }
    };
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsx("h1", { className: "page-title", children: "Gest\u00E3o de Empresas" }), _jsx("p", { className: "page-subtitle", children: "Cadastro e gerenciamento de empresas monitoradas" })] }), _jsxs("div", { className: "content-body", children: [_jsxs("div", { className: "card", children: [_jsxs("div", { className: "card-header", children: [_jsx("h2", { className: "card-title", children: "Empresas Cadastradas" }), _jsx("button", { className: "btn btn-primary", onClick: () => setShowForm(true), children: "\uD83C\uDFE2 Nova Empresa" })] }), _jsx("div", { className: "card-body", children: loading ? (_jsx("div", { className: "loading", children: _jsx("div", { className: "spinner" }) })) : (_jsx("div", { className: "table-responsive", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "CNPJ" }), _jsx("th", { children: "Raz\u00E3o Social" }), _jsx("th", { children: "Nome Fantasia" }), _jsx("th", { children: "Monitorada" }), _jsx("th", { children: "Pasta Origem" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "A\u00E7\u00F5es" })] }) }), _jsx("tbody", { children: empresas.map((empresa) => (_jsxs("tr", { children: [_jsx("td", { children: formatCNPJ(empresa.cnpj) }), _jsx("td", { children: empresa.razao_social }), _jsx("td", { children: empresa.nome_fantasia || '-' }), _jsx("td", { children: _jsx("span", { className: `badge ${empresa.monitorada ? 'badge-success' : 'badge-warning'}`, children: empresa.monitorada ? 'Sim' : 'Não' }) }), _jsx("td", { children: empresa.pasta_origem || '-' }), _jsx("td", { children: _jsx("span", { className: `badge ${empresa.ativo ? 'badge-success' : 'badge-danger'}`, children: empresa.ativo ? 'Ativo' : 'Inativo' }) }), _jsxs("td", { children: [_jsx("button", { className: "btn btn-sm btn-warning", onClick: () => handleEdit(empresa), title: "Editar empresa", children: "\u270F\uFE0F" }), _jsx("button", { className: "btn btn-sm btn-danger", onClick: () => handleDeleteEmpresa(empresa), style: { marginLeft: '8px' }, title: "Excluir empresa", children: "\uD83D\uDDD1\uFE0F" })] })] }, empresa.id))) })] }) })) })] }), showForm && (_jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: editingEmpresa ? 'Editar Empresa' : 'Nova Empresa' }) }), _jsx("div", { className: "card-body", children: _jsxs("form", { onSubmit: handleSubmit, children: [_jsxs("div", { className: "form-row", children: [_jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "CNPJ *" }), _jsx("input", { type: "text", className: "form-control", value: formData.cnpj, onChange: (e) => setFormData({ ...formData, cnpj: e.target.value }), placeholder: "00.000.000/0000-00", required: true })] }) }), _jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Raz\u00E3o Social *" }), _jsx("input", { type: "text", className: "form-control", value: formData.razao_social, onChange: (e) => setFormData({ ...formData, razao_social: e.target.value }), required: true })] }) })] }), _jsxs("div", { className: "form-row", children: [_jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Nome Fantasia" }), _jsx("input", { type: "text", className: "form-control", value: formData.nome_fantasia, onChange: (e) => setFormData({ ...formData, nome_fantasia: e.target.value }) })] }) }), _jsx("div", { className: "form-col", children: _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Pasta de Origem" }), _jsxs("div", { style: { display: 'flex', gap: '10px' }, children: [_jsx("input", { type: "text", className: "form-control", value: formData.pasta_origem, onChange: (e) => setFormData({ ...formData, pasta_origem: e.target.value }), placeholder: "/caminho/para/pasta", style: { flex: 1 } }), _jsx("button", { type: "button", className: "btn btn-secondary", onClick: () => {
                                                                            setShowDirBrowser(true);
                                                                            loadDirectorios(formData.pasta_origem || '/');
                                                                        }, children: "\uD83D\uDCC1 Buscar" })] })] }) })] }), _jsxs("div", { className: "form-row", children: [_jsx("div", { className: "form-col", children: _jsx("div", { className: "form-group", children: _jsxs("label", { className: "form-label", children: [_jsx("input", { type: "checkbox", checked: formData.monitorada, onChange: (e) => setFormData({ ...formData, monitorada: e.target.checked }), style: { marginRight: '8px' } }), "Empresa Monitorada"] }) }) }), _jsx("div", { className: "form-col", children: _jsx("div", { className: "form-group", children: _jsxs("label", { className: "form-label", children: [_jsx("input", { type: "checkbox", checked: formData.ativo, onChange: (e) => setFormData({ ...formData, ativo: e.target.checked }), style: { marginRight: '8px' } }), "Empresa Ativa"] }) }) })] }), _jsxs("div", { style: { display: 'flex', gap: '10px', justifyContent: 'flex-end' }, children: [_jsx("button", { type: "button", className: "btn btn-secondary", onClick: resetForm, children: "Cancelar" }), _jsx("button", { type: "submit", className: "btn btn-primary", children: editingEmpresa ? 'Atualizar' : 'Cadastrar' })] })] }) })] })), showDirBrowser && (_jsx("div", { className: "modal-overlay", onClick: () => setShowDirBrowser(false), children: _jsxs("div", { className: "modal", onClick: (e) => e.stopPropagation(), children: [_jsxs("div", { className: "modal-header", children: [_jsx("h3", { children: "Selecionar Pasta de Origem" }), _jsx("button", { className: "btn btn-sm btn-secondary", onClick: () => setShowDirBrowser(false), children: "\u2715" })] }), _jsxs("div", { className: "modal-body", children: [_jsxs("div", { style: { marginBottom: '15px' }, children: [_jsx("strong", { children: "Caminho atual:" }), " ", currentPath] }), loadingDir ? (_jsxs("div", { className: "loading", children: [_jsx("div", { className: "spinner" }), _jsx("p", { children: "Carregando diret\u00F3rios..." })] })) : (_jsx("div", { className: "directory-list", style: { maxHeight: '300px', overflowY: 'auto' }, children: diretorios.map((dir, index) => (_jsxs("div", { className: "directory-item", style: {
                                                    padding: '10px',
                                                    borderBottom: '1px solid #eee',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center'
                                                }, onClick: () => handleSelectDirectory(dir), onMouseEnter: (e) => e.currentTarget.style.backgroundColor = '#f5f5f5', onMouseLeave: (e) => e.currentTarget.style.backgroundColor = 'transparent', children: [_jsx("span", { style: { marginRight: '10px' }, children: dir.tipo === 'voltar' ? '⬅️' : '📁' }), _jsx("span", { children: dir.nome })] }, index))) }))] }), _jsxs("div", { className: "modal-footer", children: [_jsx("button", { className: "btn btn-secondary", onClick: () => setShowDirBrowser(false), children: "Cancelar" }), _jsx("button", { className: "btn btn-primary", onClick: handleUseDirectory, children: "Usar Este Diret\u00F3rio" })] })] }) }))] })] }));
};
