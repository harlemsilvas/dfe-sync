import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export const ProductsTable = ({ produtos }) => {
    if (!produtos || produtos.length === 0) {
        return _jsx("div", { style: { fontStyle: "italic" }, children: "Nenhum produto parseado." });
    }
    return (_jsxs("table", { style: { width: "100%", borderCollapse: "collapse" }, children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "#" }), _jsx("th", { children: "C\u00F3digo" }), _jsx("th", { children: "Descri\u00E7\u00E3o" }), _jsx("th", { children: "NCM" }), _jsx("th", { children: "CFOP" }), _jsx("th", { children: "Qtde" }), _jsx("th", { children: "Valor Total" })] }) }), _jsx("tbody", { children: produtos.map((p, idx) => (_jsxs("tr", { style: { borderTop: "1px solid #ddd" }, children: [_jsx("td", { children: p.numero_item || idx + 1 }), _jsx("td", { children: p.codigo || "" }), _jsx("td", { children: p.descricao || "" }), _jsx("td", { children: p.ncm || "" }), _jsx("td", { children: p.cfop || "" }), _jsx("td", { children: p.quantidade ?? "" }), _jsx("td", { children: p.valor_total ?? (p.valor || "") })] }, idx))) })] }));
};
