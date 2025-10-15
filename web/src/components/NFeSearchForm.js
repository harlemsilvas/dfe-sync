import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
export const NFeSearchForm = ({ onSearch, loading }) => {
    const [chave, setChave] = useState("");
    const [error, setError] = useState(null);
    function submit(e) {
        e.preventDefault();
        const digits = chave.replace(/\D/g, "");
        if (digits.length !== 44) {
            setError("Chave deve ter 44 dígitos");
            return;
        }
        setError(null);
        onSearch(digits);
    }
    return (_jsxs("form", { onSubmit: submit, className: "nfe-search-form", style: { display: "flex", gap: 8, flexWrap: "wrap" }, children: [_jsx("input", { type: "text", placeholder: "Chave NF-e (44 d\u00EDgitos)", value: chave, onChange: (e) => setChave(e.target.value), style: { flex: "1 1 320px", padding: 8 }, disabled: loading }), _jsx("button", { type: "submit", disabled: loading, style: { padding: "8px 16px" }, children: loading ? "Consultando..." : "Consultar" }), error && _jsx("div", { style: { color: "red", width: "100%" }, children: error })] }));
};
