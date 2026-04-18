#!/usr/bin/env python3
"""
Hace admin a un usuario existente.
Uso: python scripts/make_admin.py EMAIL
"""
import sys
sys.path.insert(0, "/app")

if len(sys.argv) < 2:
    print("❌ Uso: make create-admin EMAIL=tu@correo.com")
    sys.exit(1)

email = sys.argv[1]

from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.email == email).first()
if not user:
    print(f"❌ Usuario no encontrado: {email}")
    sys.exit(1)

user.role = "admin"
db.commit()
print(f"✅ {user.full_name} ({user.email}) ahora es admin")
