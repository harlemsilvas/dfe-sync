#!/usr/bin/env python3
"""Diagnóstico do storage de XMLs"""
import os
from pathlib import Path

PROJECT_ROOT = Path("/mnt/c/Projetos/dfe-sync")
print(f"📁 Projeto: {PROJECT_ROOT}")
print(f"   Existe? {PROJECT_ROOT.exists()}")

# Verificar storage
storage = PROJECT_ROOT / "storage"
print(f"\n📦 storage/: {storage.exists()}")
if storage.exists():
    for item in storage.iterdir():
        print(f"   - {item.name:20s} {'(dir)' if item.is_dir() else f'{item.stat().st_size/1024:.1f}KB'}")

# Verificar XMLs
xml_dir = storage / "xml"
print(f"\n📄 storage/xml/: {xml_dir.exists()}")
if xml_dir.exists():
    xmls = list(xml_dir.rglob("*.xml"))
    print(f"   Total XMLs: {len(xmls)}")
    if xmls:
        print(f"   Exemplo: {xmls[0].relative_to(PROJECT_ROOT)}")
        print(f"   Conteúdo exemplo:")
        print(xmls[0].read_text()[:300] + "...")
else:
    print("   ❌ Diretório não existe - crie com: mkdir -p storage/xml")