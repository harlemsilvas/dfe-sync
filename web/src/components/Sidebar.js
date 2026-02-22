import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NavLink } from 'react-router-dom';
export const Sidebar = () => {
    const menuItems = [
        {
            path: '/',
            label: 'Dashboard',
            icon: '📊',
        },
        {
            path: '/empresas',
            label: 'Empresas',
            icon: '🏢',
        },
        {
            path: '/certificados',
            label: 'Certificados',
            icon: '🔐',
        },
        {
            path: '/cfops',
            label: 'CFOPs',
            icon: '📋',
        },
        {
            path: '/importacao',
            label: 'Importação',
            icon: '📁',
        },
        {
            path: '/classificacao',
            label: 'Classificação',
            icon: '🔄',
        },
        {
            path: '/relatorios',
            label: 'Relatórios',
            icon: '📈',
        },
        {
            path: '/logs',
            label: 'Logs',
            icon: '📝',
        },
        {
            path: '/configuracoes',
            label: 'Configurações',
            icon: '⚙️',
        },
    ];
    return (_jsxs("nav", { className: "sidebar", children: [_jsxs("div", { className: "sidebar-header", children: [_jsx("h1", { className: "sidebar-title", children: "DFE Sync" }), _jsx("p", { className: "sidebar-subtitle", children: "Sistema de Gest\u00E3o" })] }), _jsx("ul", { className: "sidebar-menu", children: menuItems.map((item) => (_jsx("li", { children: _jsxs(NavLink, { to: item.path, className: ({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`, end: item.path === '/', children: [_jsx("span", { className: "sidebar-item-icon", children: item.icon }), item.label] }) }, item.path))) })] }));
};
