import React, { useState } from "react";

interface Props {
  onSearch: (chave: string) => void;
  loading: boolean;
}

export const NFeSearchForm: React.FC<Props> = ({ onSearch, loading }) => {
  const [chave, setChave] = useState("");
  const [error, setError] = useState<string | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const digits = chave.replace(/\D/g, "");
    if (digits.length !== 44) {
      setError("Chave deve ter 44 dígitos");
      return;
    }
    setError(null);
    onSearch(digits);
  }

  return (
    <form
      onSubmit={submit}
      className="nfe-search-form"
      style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
    >
      <input
        type="text"
        placeholder="Chave NF-e (44 dígitos)"
        value={chave}
        onChange={(e) => setChave(e.target.value)}
        style={{ flex: "1 1 320px", padding: 8 }}
        disabled={loading}
      />
      <button type="submit" disabled={loading} style={{ padding: "8px 16px" }}>
        {loading ? "Consultando..." : "Consultar"}
      </button>
      {error && <div style={{ color: "red", width: "100%" }}>{error}</div>}
    </form>
  );
};
