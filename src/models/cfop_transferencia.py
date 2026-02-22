from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Text
from src.store.db import Base

class CfopTransferencia(Base):
    __tablename__ = "cfops_transferencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(4), unique=True, nullable=False, index=True)  # Ex: 5949, 5152
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_operacao: Mapped[str] = mapped_column(String(50), nullable=False)  # Ex: "Depósito Temporário", "Transferência"
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<CfopTransferencia(codigo='{self.codigo}', tipo_operacao='{self.tipo_operacao}')>"