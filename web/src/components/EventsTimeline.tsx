import React from "react";

interface Props {
  eventos?: any[];
}

export const EventsTimeline: React.FC<Props> = ({ eventos }) => {
  if (!eventos || eventos.length === 0) {
    return <div style={{ fontStyle: "italic" }}>Sem eventos.</div>;
  }
  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {eventos.map((e, i) => (
        <li key={i} style={{ marginBottom: 4 }}>
          <span>• {e.descricao}</span>
        </li>
      ))}
    </ul>
  );
};
