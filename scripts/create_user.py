#!/usr/bin/env python3
"""
Crea un usuario nuevo desde la línea de comandos.
Uso: python scripts/create_user.py EMAIL "Nombre Completo" "Nombre Org" PASSWORD
"""
import sys
sys.path.insert(0, "/app")

if len(sys.argv) < 5:
    print("❌ Uso: make create-user EMAIL=x NAME='x' ORG='x' PASS=x")
    sys.exit(1)

email, full_name, org_name, password = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

from slugify import slugify
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User

db = SessionLocal()

if db.query(User).filter(User.email == email).first():
    print(f"❌ Email ya registrado: {email}")
    sys.exit(1)

base_slug = slugify(org_name)
slug = base_slug
counter = 1
while db.query(Organization).filter(Organization.slug == slug).first():
    slug = f"{base_slug}-{counter}"
    counter += 1

org = Organization(name=org_name, slug=slug)
org.set_trial()
db.add(org)
db.flush()

user = User(
    organization_id=org.id,
    email=email,
    hashed_password=hash_password(password),
    full_name=full_name,
)
db.add(user)
db.commit()
print(f"✅ Usuario creado: {email} en org \"{org_name}\"")
