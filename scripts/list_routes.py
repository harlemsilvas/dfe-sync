#!/usr/bin/env python3
# uso: python scripts/list_routes.py
import sys
sys.path.insert(0, "/mnt/c/Projetos/dfe-sync")

from src.api.main import app

print("📊 Rotas registradas:")
print("=" * 80)
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['GET'])
        print(f"  {str(list(methods)):25} {route.path}")
print("=" * 80)