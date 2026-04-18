"""
Schemas de autenticación — formas de los datos que entran y salen de la API.

¿Qué es un schema de Pydantic?
  Un schema define la forma (shape) de los datos. Cuando FastAPI recibe
  un request con JSON, Pydantic valida automáticamente que tenga los
  campos correctos con los tipos correctos. Si no, retorna un 422 claro
  antes de que tu código corra.

  Esto es distinto a los modelos SQLAlchemy:
    - Modelos SQLAlchemy → representan tablas en la DB
    - Schemas Pydantic   → representan datos en la API (requests y responses)
  
  Un schema puede incluir campos que no están en el modelo, excluir
  campos sensibles (como hashed_password), o combinar datos de
  múltiples modelos.

Convención de nombres:
  UserCreate   → datos para crear un recurso (request body)
  UserResponse → datos que retorna la API (response body)
  UserLogin    → datos para autenticarse

¿Por qué no retornar el modelo SQLAlchemy directamente?
  Porque incluiría hashed_password en la respuesta.
  El schema UserResponse define exactamente qué campos expones.
"""

import uuid

from pydantic import BaseModel, EmailStr, field_validator


# ── Register ──────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    """Datos de la ferretería al registrarse."""
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class UserRegisterRequest(BaseModel):
    """
    Body del POST /auth/register.
    
    EmailStr es un tipo especial de Pydantic que valida que el
    string tenga formato de email válido. Si mandas "no-es-email",
    Pydantic retorna 422 automáticamente.
    """
    full_name: str
    email: EmailStr
    password: str
    organization_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("El password debe tener al menos 8 caracteres")
        return v

    @field_validator("full_name", "organization_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo no puede estar vacío")
        return v.strip()


# ── Login ─────────────────────────────────────────────────

class UserLoginRequest(BaseModel):
    """Body del POST /auth/login."""
    email: EmailStr
    password: str


# ── Responses ─────────────────────────────────────────────

class OrganizationResponse(BaseModel):
    """Datos de la organización que se devuelven al cliente."""
    id: uuid.UUID
    name: str
    slug: str

    # model_config con from_attributes=True permite crear este schema
    # desde un objeto SQLAlchemy (no solo desde un dict)
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """
    Datos del usuario que se devuelven al cliente.
    Nótese que hashed_password NO está aquí — nunca se expone.
    """
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    organization: OrganizationResponse

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """
    Respuesta del login y register exitoso.
    
    access_token: el JWT que el frontend guardará y mandará en futuros requests
    token_type: siempre "bearer" — es el estándar HTTP para tokens en el header
                Authorization: Bearer <token>
    user: datos del usuario para que el frontend los muestre sin hacer otra request
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
