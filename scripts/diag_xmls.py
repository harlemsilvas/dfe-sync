#!/usr/bin/env python3
"""Diagnóstico do storage de XMLs SEM depender do FastAPI"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path("/mnt/c/Projetos/dfe-sync")
print(f"📁 Projeto: {PROJECT_ROOT}")
print(f"   Existe? {PROJECT_ROOT.exists()}\n")

# Buscar XMLs
print("🔍 Procurando XMLs...")
xmls_found = []
for root, dirs, files in os.walk(PROJECT_ROOT, topdown=True):
    # Pular diretórios irrelevantes
    if any(p.startswith((".", "_", "venv", ".git", "__pycache__", "node_modules")) 
           for p in Path(root).parts):
        continue
    
    for file in files:
        if file.endswith(".xml"):
            xmls_found.append(Path(root) / file)
            if len(xmls_found) >= 5:  # Mostrar só 5 exemplos
                break
    if len(xmls_found) >= 5:
        break

if xmls_found:
    print(f"\n✅ Encontrados {len(xmls_found)}+ XMLs:")
    for xml in xmls_found:
        rel_path = xml.relative_to(PROJECT_ROOT)
        print(f"   • {rel_path}")
    
    # Mostrar estrutura do primeiro XML
    print(f"\n📄 Exemplo do primeiro XML ({xmls_found[0].name}):")
    try:
        content = xmls_found[0].read_text(encoding="utf-8", errors="ignore")
        print(content[:500] + "...")
    except Exception as e:
        print(f"   ❌ Erro ao ler: {e}")
else:
    print("\n❌ Nenhum XML encontrado!")
    print("\n💡 Dica: Crie a estrutura padrão:")
    print("   mkdir -p storage/xml")
    print("   # E coloque alguns XMLs de teste lá")