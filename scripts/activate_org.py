#!/usr/bin/env python3
"""
Activa la suscripción de una organización dado el email de uno de sus usuarios.
Uso: python scripts/activate_org.py EMAIL
"""
import sys
sys.path.insert(0, "/app")

if len(sys.argv) < 2:
    print("❌ Uso: make activate-org EMAIL=correo@cliente.com")
    sys.exit(1)

email = sys.argv[1]

from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy.orm import joinedload

db = SessionLocal()
user = (
    db.query(User)
    .options(joinedload(User.organization))
    .filter(User.email == email)
    .first()
)

if not user:
    print(f"❌ Usuario no encontrado: {email}")
    sys.exit(1)

org = user.organization
org.subscription_status = "active"
org.subscribed_at = datetime.now(timezone.utc)
db.commit()
print(f"✅ Org \"{org.name}\" activada correctamente")
