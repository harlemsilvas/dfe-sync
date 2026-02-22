import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Empresas } from './pages/Cadastros/Empresas';
import Certificados from './pages/Cadastros/Certificados';
import { CFOPs } from './pages/Cadastros/CFOPs';
import { Importacao } from './pages/Importacao/Importacao';
import { Classificacao } from './pages/Classificacao/Classificacao';
import { Relatorios } from './pages/Relatorios/Relatorios';
import { Logs } from './pages/Relatorios/Logs';
import { Configuracoes } from './pages/Configuracoes/Configuracoes';
import { XMLViewer } from './pages/Classificacao/XMLViewer';
import './App.css';
export const App = () => {
    return (_jsx(Router, { children: _jsx(Layout, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Dashboard, {}) }), _jsx(Route, { path: "/empresas", element: _jsx(Empresas, {}) }), _jsx(Route, { path: "/certificados", element: _jsx(Certificados, {}) }), _jsx(Route, { path: "/cfops", element: _jsx(CFOPs, {}) }), _jsx(Route, { path: "/importacao", element: _jsx(Importacao, {}) }), _jsx(Route, { path: "/classificacao", element: _jsx(Classificacao, {}) }), _jsx(Route, { path: "/xml-viewer/:id", element: _jsx(XMLViewer, {}) }), _jsx(Route, { path: "/relatorios", element: _jsx(Relatorios, {}) }), _jsx(Route, { path: "/logs", element: _jsx(Logs, {}) }), _jsx(Route, { path: "/configuracoes", element: _jsx(Configuracoes, {}) })] }) }) }));
};
