"""
Middleware de suscripción.

¿Cómo funciona FastAPI con middlewares?
  Un middleware es una función que envuelve CADA request. Recibe el
  request antes de que llegue al endpoint, puede modificarlo o
  bloquearlo, y recibe la response antes de que llegue al cliente.

  El patrón es:
    1. request entra al middleware
    2. middleware decide si llama a call_next(request)
       - Si llama → el request llega al endpoint normalmente
       - Si no llama → retorna una respuesta directamente (ej: 403)
    3. la response pasa de vuelta por el middleware

¿Por qué no verificar en cada Depends() en lugar de middleware?
  La dependency get_current_user ya verifica autenticación (JWT válido).
  Si también verificara suscripción, mezclaría dos responsabilidades
  distintas en un solo lugar — más difícil de mantener.

  Con middleware separado:
    - get_current_user → verifica identidad (¿quién eres?)
    - SubscriptionMiddleware → verifica acceso (¿puedes usar esto?)
  
  Separación de responsabilidades limpia.

Rutas excluidas del check de suscripción:
  - /api/v1/auth/* → login y registro siempre deben funcionar
  - /health        → para que Docker pueda verificar que el servidor vive
  - /docs, /redoc  → Swagger en desarrollo
  - /api/v1/admin/* → el admin necesita acceso aunque la org esté expirada
                      para poder reactivarla
"""

import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Rutas que NO pasan por el check de suscripción
EXCLUDED_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/admin/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


class SubscriptionMiddleware(BaseHTTPMiddleware):
    """
    Verifica que la organización del usuario tenga suscripción activa.
    Si el trial venció o la cuenta está expirada, retorna 403.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Dejar pasar rutas excluidas sin verificar
        for prefix in EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Solo verificar rutas de la API que requieren autenticación
        if not path.startswith("/api/"):
            return await call_next(request)

        # Obtener el usuario del estado del request
        # (FastAPI lo pone ahí después de procesar el JWT en la dependency)
        # Como el middleware corre ANTES que las dependencies, no tenemos
        # el usuario aún. Lo obtenemos del token directamente.
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            # Sin token → dejar pasar (el endpoint lo rechazará con 401)
            return await call_next(request)

        # Decodificar el token para obtener org_id sin tocar la DB
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload:
            return await call_next(request)

        org_id_str = payload.get("org_id")
        if not org_id_str:
            return await call_next(request)

        # Verificar suscripción en la DB
        # Usamos una sesión directa — no podemos usar Depends() en middleware
        from app.core.database import SessionLocal
        from app.models.organization import Organization
        import uuid

        try:
            org_id = uuid.UUID(org_id_str)
        except ValueError:
            return await call_next(request)

        db = SessionLocal()
        try:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if org and not org.has_access:
                # Organización sin acceso — retornar 403 con info útil
                body = json.dumps({
                    "detail": "subscription_expired",
                    "subscription_status": org.subscription_status,
                    "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
                })
                return Response(
                    content=body,
                    status_code=403,
                    media_type="application/json",
                )
        finally:
            db.close()

        return await call_next(request)
