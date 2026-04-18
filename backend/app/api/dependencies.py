"""
Dependencies de FastAPI para autenticación.

Una 'dependency' en FastAPI es una función que se ejecuta automáticamente
antes del endpoint que la declare. Si la dependency lanza una excepción
(como HTTPException 401), el endpoint nunca corre.

Esto implementa el patrón 'Bearer Token':
  El cliente manda el JWT en el header de cada request:
    Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
  
  FastAPI extrae el token con OAuth2PasswordBearer,
  lo decodifica, verifica la firma, busca al usuario en DB,
  y lo inyecta en el endpoint.

¿Por qué OAuth2PasswordBearer si no implementamos OAuth2 completo?
  OAuth2PasswordBearer es simplemente una clase de FastAPI que:
    1. Lee el header Authorization: Bearer <token>
    2. Retorna el token como string
    3. Documenta automáticamente en Swagger que el endpoint requiere auth
  
  No implementa el flujo OAuth2 completo — solo reutiliza la convención
  del header que OAuth2 Bearer define. Es el estándar para APIs REST.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# tokenUrl indica a FastAPI dónde está el endpoint de login
# Solo se usa para la documentación de Swagger — no afecta la lógica
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency principal de autenticación.
    
    FastAPI llama a esta función antes de cada endpoint que la declare.
    Recibe el token del header, lo decodifica, y retorna el usuario de la DB.
    
    Si algo falla (token inválido, expirado, usuario no existe, inactivo),
    lanza 401 y el endpoint nunca corre.
    
    Uso en un endpoint:
        @router.get("/mis-catalogos")
        def mis_catalogos(current_user: User = Depends(get_current_user)):
            # current_user ya está verificado y es el objeto User de la DB
            return get_catalogs(current_user.organization_id)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido",
        # WWW-Authenticate es el header estándar para indicar el esquema de auth
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decodificar y verificar el JWT
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # 2. Extraer el user_id del payload
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # 3. Convertir string a UUID (si no es UUID válido, el token fue manipulado)
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # 4. Buscar el usuario en la base de datos
    # Usamos joinedload para cargar la organización en la misma query
    # Sin esto, acceder a user.organization haría una segunda query (N+1 problem)
    from sqlalchemy.orm import joinedload
    user = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    # 5. Verificar que el usuario está activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Alias semántico de get_current_user.
    
    Algunos endpoints lo usan para dejar claro en el código
    que requieren un usuario activo (vs endpoints que podrían
    funcionar con usuarios inactivos en el futuro).
    """
    return current_user
