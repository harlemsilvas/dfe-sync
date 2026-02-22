from pydantic import BaseModel

class CertificadoBase(BaseModel):
    cnpj: str

class CertificadoCreate(CertificadoBase):
    pfx_password: str

class Certificado(CertificadoBase):
    id: int

    class Config:
        from_attributes = True
