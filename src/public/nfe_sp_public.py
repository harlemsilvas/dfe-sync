import re, time, hashlib, datetime
from typing import Optional, Dict, Any
import requests
from lxml import html


class SPNFePublicClient:
    """Cliente para consulta pública resumida de NF-e no portal da SEFAZ/SP.

    Observações:
    - Página sujeita a alterações de layout e possíveis captchas. Este código tenta detectar sinais de captcha e retorna status apropriado.
    - Uso moderado recomendado (intervalo mínimo entre a mesma chave configurável).
    - Apenas para chaves cujo acesso o usuário já possui (compliance / evitar scraping abusivo).
    """

    BASE_URL = "https://nfe.fazenda.sp.gov.br/ConsultaNFe/consulta/publica/ConsultarNFe.aspx"

    def __init__(self, min_interval_sec: int = 2, timeout: int = 30, user_agent: str = "Mozilla/5.0 (compatible; dfe-sync/0.1)"):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "close",
        })
        self.min_interval_sec = min_interval_sec
        self.timeout = timeout
        self._last_fetch: Dict[str, float] = {}

    def _rate_limit(self, chave: str):
        now = time.time()
        last = self._last_fetch.get(chave)
        if last and (now - last) < self.min_interval_sec:
            time.sleep(self.min_interval_sec - (now - last))
        self._last_fetch[chave] = time.time()

    @staticmethod
    def _clean_text(t: Optional[str]) -> Optional[str]:
        if t is None:
            return None
        return re.sub(r"\s+", " ", t).strip()

    def _detect_captcha(self, tree: html.HtmlElement) -> bool:
        txt = tree.text_content().lower()
        if "captcha" in txt or "digite os caracteres" in txt:
            return True
        # Possível imagem de captcha
        if tree.xpath("//img[contains(@src,'captcha')]"):
            return True
        return False

    def _parse_products(self, tree: html.HtmlElement) -> list[dict[str, Any]]:
        """Tenta localizar tabela de produtos e extrair linhas.

        Heurísticas:
        - Procurar tabelas contendo cabeçalhos com palavras-chave (código, descrição, ncm, cfop, quantidade, valor).
        - Flexível a variações de acentuação e caixa.
        - Tentar converter números (quantidade, valores) para float.
        - Falhas de parsing retornam lista vazia silenciosamente.
        """
        keywords = ["código", "codigo", "descr", "ncm", "cfop", "quant", "valor"]
        tables = tree.xpath("//table")
        chosen = None
        header_map: dict[int, str] = {}
        for tbl in tables:
            headers = [self._clean_text(h.text_content()).lower() for h in tbl.xpath(".//th")]
            if not headers:
                # algumas páginas usam primeira linha <tr><td> como cabeçalho
                first_tr_tds = [self._clean_text(td.text_content()).lower() for td in tbl.xpath(".//tr[1]/td")]
                if first_tr_tds:
                    headers = first_tr_tds
            if not headers:
                continue
            score = sum(any(kw in (h or '') for kw in keywords) for h in headers)
            if score >= 3:  # limiar mínimo
                chosen = tbl
                # mapear índice -> header base
                for idx, h in enumerate(headers):
                    for base in ["codigo", "descr", "ncm", "cfop", "quant", "valor", "un"]:
                        if h and base in h.replace("ção","cao").replace("ç","c"):
                            header_map[idx] = base
                break
        if chosen is None:
            return []
        items: list[dict[str, Any]] = []
        rows = chosen.xpath(".//tr")[1:]  # pular cabeçalho
        item_n = 0
        for r in rows:
            cols = [self._clean_text(td.text_content()) for td in r.xpath(".//td")]
            if not cols or all(c == '' for c in cols):
                continue
            item_n += 1
            data: dict[str, Any] = {"numero_item": item_n}
            for idx, val in enumerate(cols):
                key = header_map.get(idx)
                if not key:
                    continue
                vnorm = val
                if key in ("quant", "valor"):
                    # substituir separador decimal vírgula
                    vn = vnorm.replace(".", "").replace(",", ".")
                    try:
                        num = float(re.sub(r"[^0-9\.]+", "", vn))
                    except ValueError:
                        num = None
                    vnorm = num
                if key == "descr":
                    key = "descricao"
                elif key == "codigo":
                    key = "codigo"
                elif key == "quant":
                    key = "quantidade"
                elif key == "valor":
                    # decidir se é unit ou total: heurística - primeiro valor encontrado vira valor_total se não houver mais colunas distintas
                    # aqui armazenamos temporário e ajustamos depois
                    pass
                data[key] = vnorm
            items.append(data)
        # Ajuste valores unitário/total se possível (heurística simples)
        for it in items:
            if 'quantidade' in it:
                # heurística futura para separar valor_unitario/valor_total
                pass
        return items

    def _parse_sections(self, tree: html.HtmlElement) -> Dict[str, Any]:
        # Estruturas prováveis -> placeholders de seletores que podem ser ajustados
        text_full = tree.text_content()
        data: Dict[str, Any] = {}

        # Chave: 44 dígitos
        m_chave = re.search(r"(\d{44})", text_full)
        if m_chave:
            data["chave"] = m_chave.group(1)

        # Tentar capturar blocos emitente/destinatario usando regex heurística (melhorar com inspeção de spans/classes se disponíveis)
        def extract_party(label: str):
            # Busca label seguido de algumas linhas
            pattern = re.compile(label + r".*?CNPJ:?\s*(\d{14}).*?IE:?\s*([0-9A-Z\.\-]+)?.*?Munic[ií]pio:?\s*([^\n]+?)\s+UF:?\s*([A-Z]{2})", re.IGNORECASE | re.DOTALL)
            mm = pattern.search(text_full)
            if mm:
                return {
                    "cnpj": mm.group(1),
                    "ie": (mm.group(2) or '').strip(),
                    "municipio": mm.group(3).strip(),
                    "uf": mm.group(4).strip()
                }
            return None

        data["emitente"] = extract_party("Emitente")
        data["destinatario"] = extract_party("Destinat[aá]rio")

        # Produtos (heurístico)
        data["produtos"] = self._parse_products(tree)

        # Eventos: procurar palavras 'Evento' e possível protocolo
        eventos = []
        for bloco in re.findall(r"Evento[:\s]+(.{0,120})", text_full):
            ev = bloco.strip().splitlines()[0]
            if ev:
                eventos.append({"descricao": self._clean_text(ev)})
        data["eventos"] = eventos

        return data

    def consulta_publica_chave(self, chave: str) -> Dict[str, Any]:
        chave = re.sub(r"\D", "", chave)
        if len(chave) != 44:
            return {"status": "error", "detail": "chave_invalida"}
        self._rate_limit(chave)
        try:
            # Passo 1: GET inicial (cookies / viewstate se necessário)
            resp = self.session.get(self.BASE_URL, timeout=self.timeout)
            if resp.status_code >= 500:
                return {"status": "error", "detail": f"http_{resp.status_code}_initial"}
            # Sem viewstate handling por enquanto (placeholder). Se necessário, extrair hidden inputs.

            # Passo 2: Submeter chave.
            # Sem HTML do form real, tentamos GET com parâmetro nfe=<chave>. Ajustaremos se necessário.
            params = {"nfe": chave}
            resp2 = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
            if resp2.status_code == 404:
                return {"status": "not_found"}
            if resp2.status_code >= 500:
                return {"status": "error", "detail": f"http_{resp2.status_code}"}

            tree = html.fromstring(resp2.text)
            if self._detect_captcha(tree):
                return {"status": "captcha_required"}

            data = self._parse_sections(tree)
            if "chave" not in data:
                return {"status": "not_found"}

            raw_hash = hashlib.sha256(resp2.text.encode('utf-8', errors='ignore')).hexdigest()
            data.update({
                "status": "ok",
                "raw_html_hash": f"sha256:{raw_hash}",
                "fetched_at": datetime.datetime.utcnow().isoformat() + 'Z'
            })
            return data
        except requests.RequestException as e:
            return {"status": "error", "detail": str(e)}


_default_client: Optional[SPNFePublicClient] = None

def consulta_publica_sp(chave: str) -> Dict[str, Any]:
    global _default_client
    if _default_client is None:
        _default_client = SPNFePublicClient()
    return _default_client.consulta_publica_chave(chave)
