import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Sidebar } from './Sidebar';
export const Layout = ({ children }) => {
    return (_jsxs("div", { className: "layout", children: [_jsx(Sidebar, {}), _jsx("main", { className: "main-content", children: children })] }));
};
