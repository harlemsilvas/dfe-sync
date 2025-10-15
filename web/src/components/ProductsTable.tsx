import React from "react";
import { NFePublicResponse } from "../api/client";

interface Props {
  produtos?: any[];
}

export const ProductsTable: React.FC<Props> = ({ produtos }) => {
  if (!produtos || produtos.length === 0) {
    return <div style={{ fontStyle: "italic" }}>Nenhum produto parseado.</div>;
  }
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th>#</th>
          <th>Código</th>
          <th>Descrição</th>
          <th>NCM</th>
          <th>CFOP</th>
          <th>Qtde</th>
          <th>Valor Total</th>
        </tr>
      </thead>
      <tbody>
        {produtos.map((p, idx) => (
          <tr key={idx} style={{ borderTop: "1px solid #ddd" }}>
            <td>{p.numero_item || idx + 1}</td>
            <td>{p.codigo || ""}</td>
            <td>{p.descricao || ""}</td>
            <td>{p.ncm || ""}</td>
            <td>{p.cfop || ""}</td>
            <td>{p.quantidade ?? ""}</td>
            <td>{p.valor_total ?? (p.valor || "")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
