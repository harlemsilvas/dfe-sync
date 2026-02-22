"""
Adapter NFS-e Municipal (São Paulo/ISS): placeholder.
Cada prefeitura/provedor tem API distinta; padronize via interface comum.
"""
class NFSeSPClient:
    def __init__(self, token:str):
        self.token = token
    def listar(self, cnpj:str, inicio:str, fim:str):
        return {"items":[]}
