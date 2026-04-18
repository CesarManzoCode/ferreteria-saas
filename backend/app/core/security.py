"""
Utilidades de seguridad: hashing de passwords y manejo de JWT.

Este módulo es puramente funcional — no tiene estado, no depende de
la base de datos. Solo transforma datos: texto → hash, datos → token.

¿Por qué bcrypt para passwords?
  Los algoritmos de hash normales (MD5, SHA256) son rápidos — diseñados
  para hashear archivos grandes velozmente. Eso es malo para passwords:
  un atacante puede probar millones de combinaciones por segundo.
  
  bcrypt es deliberadamente lento. Tiene un 'cost factor' (rounds)
  que controla cuánto trabajo hace. rounds=12 tarda ~0.3 segundos
  por hash — irrelevante para un login, pero hace ataques de fuerza
  bruta imprácticamente lentos (años en lugar de días).

¿Por qué no guardar el SECRET_KEY en el código?
  Si alguien obtiene tu SECRET_KEY, puede generar tokens JWT válidos
  para cualquier usuario sin necesitar su password. Es la llave
  maestra del sistema. Vive solo en .env, nunca en el código.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Contexto de hashing — define el algoritmo y parámetros
# bcrypt con rounds=12 es el estándar de la industria en 2024
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Passwords ─────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Convierte un password en texto plano a un hash bcrypt.
    
    El hash incluye el salt (datos aleatorios) adentro, por lo que
    dos llamadas con el mismo password dan hashes diferentes.
    Eso es correcto — bcrypt los puede comparar igual.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si un password en texto plano coincide con un hash bcrypt.
    Retorna True si coinciden, False si no.
    
    NUNCA compares hashes directamente con ==.
    bcrypt.verify hace una comparación en tiempo constante que
    evita ataques de timing (medir cuánto tarda la comparación
    para deducir información sobre el hash).
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ───────────────────────────────────────────────────

def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    """
    Genera un JWT firmado con la información del usuario.
    
    Args:
        subject: el identificador del usuario (su UUID como string)
        extra_claims: datos adicionales a incluir en el payload
                      (ej: {"role": "owner", "org_id": "..."})
    
    Returns:
        El token JWT como string. Se manda al cliente, quien lo
        guarda y lo incluye en futuros requests.
    
    El payload estándar de JWT usa estas claves convencionales:
        sub (subject)  → identificador del usuario
        exp (expires)  → timestamp de expiración — jose lo verifica automáticamente
        iat (issued at)→ cuándo se creó (informativo)
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decodifica y verifica un JWT.
    
    Verifica automáticamente:
        - Que la firma sea válida (no fue modificado)
        - Que no haya expirado (exp)
    
    Returns:
        El payload del token si es válido, None si es inválido o expirado.
        Los endpoints nunca deben recibir None — la dependency get_current_user
        lanza 401 antes de que eso pase.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        # JWTError cubre: firma inválida, token expirado, formato inválido
        return None
