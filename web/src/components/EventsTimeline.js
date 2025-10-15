import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export const EventsTimeline = ({ eventos }) => {
    if (!eventos || eventos.length === 0) {
        return _jsx("div", { style: { fontStyle: "italic" }, children: "Sem eventos." });
    }
    return (_jsx("ul", { style: { listStyle: "none", padding: 0 }, children: eventos.map((e, i) => (_jsx("li", { style: { marginBottom: 4 }, children: _jsxs("span", { children: ["\u2022 ", e.descricao] }) }, i))) }));
};
