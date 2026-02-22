import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useParams } from 'react-router-dom';
export const XMLViewer = () => {
    const { id } = useParams();
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "content-header", children: [_jsx("h1", { className: "page-title", children: "Visualizador de XML" }), _jsx("p", { className: "page-subtitle", children: "Visualiza\u00E7\u00E3o detalhada do documento XML" })] }), _jsx("div", { className: "content-body", children: _jsxs("div", { className: "card", children: [_jsx("div", { className: "card-header", children: _jsxs("h2", { className: "card-title", children: ["XML ID: ", id] }) }), _jsx("div", { className: "card-body", children: _jsx("p", { children: "Funcionalidade em desenvolvimento..." }) })] }) })] }));
};
