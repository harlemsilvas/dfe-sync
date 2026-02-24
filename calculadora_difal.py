#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Calculadora DIFAL + FCP
Calcula o DIFAL (Diferencial de Alíquota) e FCP (Fundo de Combate à Pobreza)
para operações interestaduais no Brasil.
"""

import json
from typing import Dict, Tuple

# Tabela de ICMS interestadual e interno
TABELA_ICMS = {
    "AC": {"AC": 19, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "AL": {"AC": 12, "AL": 19, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "AM": {"AC": 12, "AL": 12, "AM": 20, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "AP": {"AC": 12, "AL": 12, "AM": 12, "AP": 18, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "BA": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 20.5, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "CE": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 20, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "DF": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 20, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "ES": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 17, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "GO": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 19, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "MA": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 22, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "MG": {"AC": 7, "AL": 7, "AM": 7, "AP": 7, "BA": 7, "CE": 7, "DF": 7, "ES": 7, "GO": 7, "MA": 7, "MG": 18, "MS": 7, "MT": 7, "PA": 7, "PB": 7, "PE": 7, "PI": 7, "PR": 12, "RJ": 7, "RN": 7, "RO": 12, "RR": 7, "RS": 12, "SC": 12, "SE": 7, "SP": 12, "TO": 7},
    "MS": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 18, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "MT": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 17, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "PA": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 19, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "PB": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 20, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "PE": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 20.5, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "PI": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 21, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "PR": {"AC": 7, "AL": 7, "AM": 7, "AP": 7, "BA": 7, "CE": 7, "DF": 7, "ES": 7, "GO": 7, "MA": 7, "MG": 12, "MS": 7, "MT": 7, "PA": 7, "PB": 7, "PE": 7, "PI": 7, "PR": 19.5, "RJ": 7, "RN": 7, "RO": 7, "RR": 7, "RS": 12, "SC": 12, "SE": 7, "SP": 12, "TO": 7},
    "RJ": {"AC": 7, "AL": 7, "AM": 7, "AP": 7, "BA": 7, "CE": 7, "DF": 7, "ES": 7, "GO": 7, "MA": 7, "MG": 12, "MS": 7, "MT": 7, "PA": 7, "PB": 7, "PE": 7, "PI": 7, "PR": 12, "RJ": 20, "RN": 7, "RO": 7, "RR": 7, "RS": 12, "SC": 12, "SE": 7, "SP": 12, "TO": 7},
    "RN": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 18, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "RO": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 19.5, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "RR": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 20, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 12},
    "RS": {"AC": 7, "AL": 7, "AM": 7, "AP": 7, "BA": 7, "CE": 7, "DF": 7, "ES": 7, "GO": 7, "MA": 7, "MG": 12, "MS": 7, "MT": 7, "PA": 7, "PB": 7, "PE": 7, "PI": 7, "PR": 12, "RJ": 12, "RN": 7, "RO": 7, "RR": 7, "RS": 17, "SC": 12, "SE": 7, "SP": 12, "TO": 7},
    "SC": {"AC": 7, "AL": 7, "AM": 7, "AP": 7, "BA": 7, "CE": 7, "DF": 7, "ES": 7, "GO": 7, "MA": 7, "MG": 12, "MS": 7, "MT": 7, "PA": 7, "PB": 7, "PE": 7, "PI": 7, "PR": 12, "RJ": 12, "RN": 7, "RO": 7, "RR": 7, "RS": 12, "SC": 17, "SE": 7, "SP": 12, "TO": 7},
    "SE": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 19, "SP": 12, "TO": 12},
    "SP": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 18, "TO": 12},
    "TO": {"AC": 12, "AL": 12, "AM": 12, "AP": 12, "BA": 12, "CE": 12, "DF": 12, "ES": 12, "GO": 12, "MA": 12, "MG": 12, "MS": 12, "MT": 12, "PA": 12, "PB": 12, "PE": 12, "PI": 12, "PR": 12, "RJ": 12, "RN": 12, "RO": 12, "RR": 12, "RS": 12, "SC": 12, "SE": 12, "SP": 12, "TO": 20}
}

# Tabela de FCP por estado
TABELA_FCP = {
    "AC": {"tem_fcp": False, "aliquota_padrao": 0},
    "AL": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "AP": {"tem_fcp": False, "aliquota_padrao": 0},
    "AM": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "BA": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "CE": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "DF": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "ES": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "GO": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "MA": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "MG": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "MS": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "MT": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "PA": {"tem_fcp": False, "aliquota_padrao": 0},
    "PB": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "PE": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "PI": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "PR": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "RJ": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "RN": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "RO": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "RR": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "RS": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "SC": {"tem_fcp": False, "aliquota_padrao": 0},
    "SE": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "SP": {"tem_fcp": True, "aliquota_padrao": 2.0},
    "TO": {"tem_fcp": True, "aliquota_padrao": 2.0}
}

ESTADOS_SEM_FCP = ["AC", "AP", "PA", "SC"]


def calcular_difal_fcp(
    origem: str,
    destino: str,
    valor_mercadoria: float,
    aliquota_fcp: float = 2.0,
    calculo_por_dentro: bool = False
) -> Dict:
    """
    Calcula o DIFAL e FCP para uma operação interestadual.
    
    Args:
        origem: UF de origem (ex: "SP")
        destino: UF de destino (ex: "MG")
        valor_mercadoria: Valor da mercadoria em R$
        aliquota_fcp: Alíquota do FCP em % (padrão: 2.0)
        calculo_por_dentro: Se True, usa cálculo "por dentro" (base majorada)
    
    Returns:
        Dicionário com todos os valores calculados
    """
    
    # Verificar FCP
    info_fcp = TABELA_FCP.get(destino, {})
    if not info_fcp.get("tem_fcp", False):
        print(f"⚠️  Atenção: {destino} não possui FCP!")
        aliquota_fcp = 0.0
    
    # Obter alíquotas
    aliquota_interestadual = TABELA_ICMS[origem][destino] / 100
    aliquota_interna = TABELA_ICMS[destino][destino] / 100
    aliquota_fcp_decimal = aliquota_fcp / 100
    
    # Cálculos
    if calculo_por_dentro:
        # Cálculo por dentro (base majorada)
        icms_interestadual = valor_mercadoria * aliquota_interestadual
        bc1 = valor_mercadoria - icms_interestadual
        bc2 = bc1 / (1 - aliquota_interna)
        icms_total = bc2 * aliquota_interna
        difal = icms_total - icms_interestadual
        fcp = bc2 * aliquota_fcp_decimal
        total = difal + fcp
        
        return {
            "valor_mercadoria": valor_mercadoria,
            "aliquota_interestadual": aliquota_interestadual * 100,
            "aliquota_interna": aliquota_interna * 100,
            "icms_interestadual": icms_interestadual,
            "bc1": bc1,
            "bc2": bc2,
            "icms_total": icms_total,
            "difal": difal,
            "fcp": fcp,
            "total_difal_fcp": total,
            "calculo_por_dentro": True
        }
    else:
        # Cálculo por fora (base simples)
        icms_interestadual = valor_mercadoria * aliquota_interestadual
        icms_total = valor_mercadoria * aliquota_interna
        difal = icms_total - icms_interestadual
        fcp = valor_mercadoria * aliquota_fcp_decimal
        total = difal + fcp
        
        return {
            "valor_mercadoria": valor_mercadoria,
            "aliquota_interestadual": aliquota_interestadual * 100,
            "aliquota_interna": aliquota_interna * 100,
            "icms_interestadual": icms_interestadual,
            "bc1": valor_mercadoria,
            "icms_total": icms_total,
            "difal": difal,
            "fcp": fcp,
            "total_difal_fcp": total,
            "calculo_por_dentro": False
        }


def imprimir_resultado(resultado: Dict, origem: str, destino: str):
    """Imprime o resultado formatado"""
    print("\n" + "="*60)
    print(f"📊 RESULTADO DO CÁLCULO DIFAL + FCP")
    print(f"   Origem: {origem} → Destino: {destino}")
    print("="*60)
    print(f"\n💰 Valor da Mercadoria:        R$ {resultado['valor_mercadoria']:.2f}")
    print(f"📈 Alíquota Interestadual:     {resultado['aliquota_interestadual']:.2f}%")
    print(f"📈 Alíquota Interna Destino:   {resultado['aliquota_interna']:.2f}%")
    print(f"\n💵 ICMS Interestadual:         R$ {resultado['icms_interestadual']:.2f}")
    print(f"📋 Base de Cálculo 1 (BC1):    R$ {resultado['bc1']:.2f}")
    
    if resultado.get('bc2'):
        print(f"📋 Base de Cálculo 2 (BC2):    R$ {resultado['bc2']:.2f}")
    
    print(f"\n💵 ICMS Total (Destino):       R$ {resultado['icms_total']:.2f}")
    print(f"🔄 DIFAL (sem FCP):            R$ {resultado['difal']:.2f}")
    
    if resultado['fcp'] > 0:
        print(f"🏛️  FCP:                        R$ {resultado['fcp']:.2f}")
    
    print("\n" + "-"*60)
    print(f"✅ TOTAL DIFAL + FCP:          R$ {resultado['total_difal_fcp']:.2f}")
    print("-"*60 + "\n")


def main():
    """Função principal com menu interativo"""
    print("\n" + "="*60)
    print("🧮 CALCULADORA DIFAL + FCP")
    print("="*60)
    
    # Listar estados
    print("\n📋 Estados disponíveis:")
    print(", ".join(sorted(TABELA_ICMS.keys())))
    print(f"\n⚠️  Estados SEM FCP: {', '.join(ESTADOS_SEM_FCP)}")
    
    while True:
        print("\n" + "-"*60)
        print("📝 NOVO CÁLCULO")
        print("-"*60)
        
        # Entrada de dados
        origem = input("\nEstado de Origem (ex: SP): ").strip().upper()
        if origem not in TABELA_ICMS:
            print(f"❌ Estado '{origem}' inválido!")
            continue
        
        destino = input("Estado de Destino (ex: MG): ").strip().upper()
        if destino not in TABELA_ICMS:
            print(f"❌ Estado '{destino}' inválido!")
            continue
        
        if origem == destino:
            print("❌ Origem e destino não podem ser iguais!")
            continue
        
        try:
            valor = float(input("Valor da Mercadoria (R$): ").strip())
            if valor <= 0:
                print("❌ Valor deve ser maior que zero!")
                continue
        except ValueError:
            print("❌ Valor inválido!")
            continue
        
        # Verificar FCP do estado de destino
        info_fcp = TABELA_FCP.get(destino, {})
        if info_fcp.get("tem_fcp", False):
            try:
                aliquota_fcp = float(input(f"Alíquota FCP (%) [padrão: 2.0]: ").strip() or "2.0")
            except ValueError:
                print("❌ Alíquota inválida! Usando 2.0%")
                aliquota_fcp = 2.0
        else:
            print(f"ℹ️  {destino} não possui FCP. Usando 0%")
            aliquota_fcp = 0.0
        
        # Tipo de cálculo
        calculo_tipo = input("Cálculo 'por dentro'? (s/N): ").strip().lower()
        calculo_por_dentro = calculo_tipo in ['s', 'sim']
        
        # Calcular
        resultado = calcular_difal_fcp(
            origem=origem,
            destino=destino,
            valor_mercadoria=valor,
            aliquota_fcp=aliquota_fcp,
            calculo_por_dentro=calculo_por_dentro
        )
        
        # Imprimir resultado
        imprimir_resultado(resultado, origem, destino)
        
        # Continuar?
        continuar = input("Realizar outro cálculo? (s/N): ").strip().lower()
        if continuar not in ['s', 'sim']:
            print("\n👋 Obrigado por usar a calculadora!\n")
            break


if __name__ == "__main__":
    main()