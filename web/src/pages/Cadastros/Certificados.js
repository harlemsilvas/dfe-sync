import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';
export default function Certificados() {
    const [certificados, setCertificados] = useState([]);
    const [empresas, setEmpresas] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [editingCertificado, setEditingCertificado] = useState(null);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        empresa_id: '',
        nome_arquivo: '',
        senha: '',
        valido_ate: '',
        ativo: true
    });
    // Carregar dados iniciais
    useEffect(() => {
        loadCertificados();
        loadEmpresas();
    }, []);
    const loadCertificados = async () => {
        try {
            setLoading(true);
            const response = await adminApi.getCertificados();
            setCertificados(response);
        }
        catch (error) {
            console.error('Erro ao carregar certificados:', error);
            alert('Erro ao carregar certificados. Verifique a conexão com a API.');
        }
        finally {
            setLoading(false);
        }
    };
    const loadEmpresas = async () => {
        try {
            const response = await adminApi.getEmpresas();
            setEmpresas(response);
        }
        catch (error) {
            console.error('Erro ao carregar empresas:', error);
            alert('Erro ao carregar empresas. Verifique a conexão com a API.');
        }
    };
    const resetForm = () => {
        setFormData({
            empresa_id: '',
            nome_arquivo: '',
            senha: '',
            valido_ate: '',
            ativo: true
        });
        setEditingCertificado(null);
        setShowForm(false);
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        // Validações
        if (!formData.empresa_id || !formData.nome_arquivo || !formData.senha || !formData.valido_ate) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;
        }
        // Validar arquivo de certificado
        const validExtensions = ['.pfx', '.p12'];
        const fileExtension = formData.nome_arquivo.toLowerCase().slice(formData.nome_arquivo.lastIndexOf('.'));
        if (!validExtensions.includes(fileExtension)) {
            alert('Arquivo inválido! Use apenas arquivos .pfx ou .p12');
            return;
        }
        try {
            setLoading(true);
            const submitData = {
                ...formData,
                empresa_id: parseInt(formData.empresa_id)
            };
            if (editingCertificado) {
                await adminApi.updateCertificado(editingCertificado.id, submitData);
                alert('Certificado atualizado com sucesso!');
            }
            else {
                await adminApi.createCertificado(submitData);
                alert('Certificado cadastrado com sucesso!');
            }
            resetForm();
            await loadCertificados();
        }
        catch (error) {
            console.error('Erro ao salvar certificado:', error);
            if (error.response?.status === 409) {
                alert('Já existe um certificado ativo para esta empresa.');
            }
            else if (error.response?.status === 404) {
                alert('Empresa não encontrada.');
            }
            else {
                alert('Erro ao salvar certificado. Tente novamente.');
            }
        }
        finally {
            setLoading(false);
        }
    };
    const handleEdit = (cert) => {
        setEditingCertificado(cert);
        setFormData({
            empresa_id: cert.empresa_id.toString(),
            nome_arquivo: cert.nome_arquivo,
            senha: '', // Não preenche a senha por segurança
            valido_ate: cert.valido_ate,
            ativo: cert.ativo
        });
        setShowForm(true);
    };
    const handleDelete = async (cert) => {
        if (!window.confirm(`Tem certeza que deseja excluir o certificado "${cert.nome_arquivo}" da empresa ${cert.empresa_nome}?`)) {
            return;
        }
        try {
            setLoading(true);
            await adminApi.deleteCertificado(cert.id);
            alert('Certificado excluído com sucesso!');
            await loadCertificados();
        }
        catch (error) {
            console.error('Erro ao excluir certificado:', error);
            alert('Erro ao excluir certificado. Tente novamente.');
        }
        finally {
            setLoading(false);
        }
    };
    const handleFileUpload = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validar extensão do arquivo
            const validExtensions = ['.pfx', '.p12'];
            const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
            if (!validExtensions.includes(fileExtension)) {
                alert('Arquivo inválido! Use apenas arquivos .pfx ou .p12');
                e.target.value = '';
                return;
            }
            setFormData({ ...formData, nome_arquivo: file.name });
        }
    };
    const getStatusCertificado = (validoAte) => {
        const hoje = new Date();
        const vencimento = new Date(validoAte);
        const diasParaVencer = Math.ceil((vencimento.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
        if (diasParaVencer < 0) {
            return { label: 'Vencido', class: 'badge-danger' };
        }
        else if (diasParaVencer <= 30) {
            return { label: 'Vencendo', class: 'badge-warning' };
        }
        else {
            return { label: 'Válido', class: 'badge-success' };
        }
    };
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsx("h1", { className: "page-title", children: "Gest\u00E3o de Certificados" }), _jsx("p", { className: "page-subtitle", children: "Cadastro e gerenciamento de certificados digitais" })] }), _jsxs("div", { className: "content-body", children: [_jsxs("div", { className: "card", children: [_jsxs("div", { className: "card-header", children: [_jsx("h2", { className: "card-title", children: "Certificados Digitais" }), _jsx("button", { className: "btn btn-primary", onClick: () => setShowForm(true), disabled: loading, children: "\uD83D\uDCC1 Novo Certificado" })] }), _jsxs("div", { className: "card-body", children: [loading && _jsx("p", { children: "Carregando..." }), certificados.length === 0 && !loading ? (_jsx("p", { className: "text-center", children: "Nenhum certificado cadastrado." })) : (_jsx("div", { className: "table-container", children: _jsxs("table", { className: "data-table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "Empresa" }), _jsx("th", { children: "CNPJ" }), _jsx("th", { children: "Arquivo" }), _jsx("th", { children: "V\u00E1lido at\u00E9" }), _jsx("th", { children: "Validade" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "A\u00E7\u00F5es" })] }) }), _jsx("tbody", { children: certificados.map((cert) => {
                                                        const status = getStatusCertificado(cert.valido_ate);
                                                        return (_jsxs("tr", { children: [_jsx("td", { children: cert.id }), _jsx("td", { children: cert.empresa_nome }), _jsx("td", { children: cert.empresa_cnpj }), _jsx("td", { children: cert.nome_arquivo }), _jsx("td", { children: new Date(cert.valido_ate).toLocaleDateString('pt-BR') }), _jsx("td", { children: _jsx("span", { className: `badge ${status.class}`, children: status.label }) }), _jsx("td", { children: _jsx("span", { className: `badge ${cert.ativo ? 'badge-success' : 'badge-danger'}`, children: cert.ativo ? 'Ativo' : 'Inativo' }) }), _jsxs("td", { children: [_jsx("button", { className: "btn btn-sm btn-warning", onClick: () => handleEdit(cert), title: "Editar certificado", children: "\u270F\uFE0F" }), _jsx("button", { className: "btn btn-sm btn-danger", onClick: () => handleDelete(cert), style: { marginLeft: '8px' }, title: "Excluir certificado", children: "\uD83D\uDDD1\uFE0F" })] })] }, cert.id));
                                                    }) })] }) }))] })] }), showForm && (_jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsx("h2", { className: "card-title", children: editingCertificado ? 'Editar Certificado' : 'Novo Certificado' }) }), _jsx("div", { className: "card-body", children: _jsxs("form", { onSubmit: handleSubmit, children: [_jsxs("div", { className: "form-row", children: [_jsxs("div", { className: "form-col", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Empresa *" }), _jsxs("select", { value: formData.empresa_id, onChange: (e) => setFormData({ ...formData, empresa_id: e.target.value }), className: "form-control", required: true, children: [_jsx("option", { value: "", children: "Selecione uma empresa..." }), empresas.map((empresa) => (_jsxs("option", { value: empresa.id, children: [empresa.razao_social, " - CNPJ: ", empresa.cnpj] }, empresa.id)))] })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Arquivo do Certificado *" }), _jsx("input", { type: "file", accept: ".pfx,.p12", onChange: handleFileUpload, className: "form-control", required: !editingCertificado }), formData.nome_arquivo && (_jsxs("small", { className: "form-text", children: ["Arquivo selecionado: ", formData.nome_arquivo] }))] })] }), _jsxs("div", { className: "form-col", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "Senha do Certificado *" }), _jsx("input", { type: "password", value: formData.senha, onChange: (e) => setFormData({ ...formData, senha: e.target.value }), className: "form-control", placeholder: "Digite a senha do certificado", required: true })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { className: "form-label", children: "V\u00E1lido at\u00E9 *" }), _jsx("input", { type: "date", value: formData.valido_ate, onChange: (e) => setFormData({ ...formData, valido_ate: e.target.value }), className: "form-control", required: true })] })] })] }), _jsx("div", { className: "form-group", children: _jsxs("div", { className: "form-check", children: [_jsx("input", { type: "checkbox", id: "ativo", checked: formData.ativo, onChange: (e) => setFormData({ ...formData, ativo: e.target.checked }), className: "form-check-input" }), _jsx("label", { htmlFor: "ativo", className: "form-check-label", children: "Certificado ativo" })] }) }), _jsxs("div", { className: "form-actions", children: [_jsx("button", { type: "submit", className: "btn btn-primary", disabled: loading, children: loading ? 'Salvando...' : editingCertificado ? 'Atualizar' : 'Cadastrar' }), _jsx("button", { type: "button", className: "btn btn-secondary", onClick: resetForm, style: { marginLeft: '8px' }, children: "Cancelar" })] })] }) })] }))] })] }));
}
