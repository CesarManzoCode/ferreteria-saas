#!/usr/bin/env python3
"""
Lista todas las organizaciones con su estado de suscripción.
Uso: python scripts/list_orgs.py
"""
import sys
sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models.organization import Organization

db = SessionLocal()
orgs = db.query(Organization).order_by(Organization.created_at.desc()).all()

if not orgs:
    print("\n  Sin organizaciones registradas.\n")
    sys.exit(0)

print(f"\n  {'Nombre':<30} {'Status':<12} {'Trial vence':<22} {'Activa'}")
print("  " + "-" * 76)

for o in orgs:
    trial = o.trial_ends_at.strftime("%d %b %Y %H:%M") if o.trial_ends_at else "-"
    acceso = "✅" if o.has_access else "❌"
    print(f"  {o.name:<30} {o.subscription_status:<12} {trial:<22} {acceso}")

print()
