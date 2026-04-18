"""
Router de autenticación — endpoints de registro y login.

¿Qué es un Router en FastAPI?
  Un Router es un agrupador de endpoints. En lugar de definir todos
  los endpoints directamente en main.py, los dividimos en routers
  por dominio (auth, catalogs, quotes). Cada router tiene su prefix
  y sus tags para organizar la documentación de Swagger.

  main.py incluye los routers:
    app.include_router(auth_router, prefix="/api/v1/auth")
  
  Y este router define las rutas relativas:
    @router.post("/register")  → POST /api/v1/auth/register
    @router.post("/login")     → POST /api/v1/auth/login

Sobre el manejo de errores:
  HTTPException de FastAPI retorna automáticamente la respuesta
  HTTP correcta con el status code y un body JSON:
    {"detail": "Email ya registrado"}
  
  El frontend puede leer ese 'detail' y mostrarlo al usuario.

Sobre slugify:
  Convierte "Ferretería García & Hijos" → "ferreteria-garcia-hijos"
  Para URLs limpias y como identificador legible en logs.
  Si el slug ya existe, añadimos un número: "ferreteria-garcia-2"
"""

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva ferretería",
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Crea una nueva organización (ferretería) y su usuario dueño.
    
    En un solo request:
      1. Verifica que el email no esté registrado
      2. Genera el slug de la organización
      3. Crea la Organization
      4. Crea el User con password hasheado
      5. Retorna el token JWT + datos del usuario
    
    Todo en una transacción: si algo falla, nada se guarda.
    """
    # 1. Verificar email único
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email ya está registrado",
        )

    # 2. Generar slug único para la organización
    base_slug = slugify(request.organization_name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # 3. Crear organización
    organization = Organization(
        name=request.organization_name,
        slug=slug,
    )
    db.add(organization)
    db.flush()  # flush envía el INSERT a la DB sin hacer commit
                # necesario para obtener el organization.id antes del commit
                # y poder asignarlo al usuario en el paso siguiente

    # 4. Crear usuario
    user = User(
        organization_id=organization.id,
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role="owner",
    )
    db.add(user)
    db.commit()

    # Refresh carga los datos actualizados desde la DB
    # (incluyendo created_at generado por PostgreSQL)
    db.refresh(user)
    db.refresh(organization)

    # Re-cargar usuario con organización para el schema de respuesta
    user.organization = organization

    # 5. Generar token
    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "org_id": str(organization.id),
            "role": user.role,
        },
    )

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Autentica un usuario existente y retorna un JWT.
    
    Nota de seguridad: el mensaje de error es genérico ("credenciales incorrectas")
    tanto si el email no existe como si el password es incorrecto.
    Dar mensajes distintos ("email no encontrado" vs "password incorrecto")
    permite a atacantes enumerar qué emails están registrados.
    """
    from sqlalchemy.orm import joinedload

    # Buscar usuario con su organización en una sola query
    user = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.email == request.email)
        .first()
    )

    # Mismo mensaje para "no existe" y "password incorrecto" — seguridad
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email o contraseña incorrectos",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise credentials_error

    if not verify_password(request.password, user.hashed_password):
        raise credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada. Contacta soporte.",
        )

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "org_id": str(user.organization_id),
            "role": user.role,
        },
    )

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener usuario autenticado",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Retorna los datos del usuario autenticado.
    
    El frontend llama esto al arrancar para saber quién está logueado
    sin tener que decodificar el JWT localmente.
    """
    return UserResponse.model_validate(current_user)
