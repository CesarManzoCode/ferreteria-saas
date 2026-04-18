"""
Configuración centralizada de la aplicación.

pydantic-settings lee variables de entorno y las valida con tipos.
Esto significa que si DATABASE_URL no está definida, la app no arranca
— falla rápido y con un mensaje claro, no a mitad de un request.

¿Por qué no usar os.environ directamente?
  os.environ["DATABASE_URL"] → si no existe, KeyError en runtime
  os.environ.get("DATABASE_URL") → si no existe, None silencioso
  
  Con pydantic-settings:
    - Tipos garantizados (str es str, int es int)
    - Validación al arrancar, no en producción
    - Documentación implícita de qué variables necesita la app
    - Soporte automático para leer desde archivo .env

Jerarquía de valores:
  1. Variables de entorno del sistema (mayor prioridad)
  2. Archivo .env
  3. Valores default en la clase (menor prioridad)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Variables de configuración de la aplicación.
    Todas las variables en mayúsculas son convención para config de entorno.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # DATABASE_URL y database_url son lo mismo
    )

    # Base de datos
    DATABASE_URL: str

    # Seguridad — JWT
    # SECRET_KEY: string largo y aleatorio para firmar los tokens JWT
    # NUNCA hardcodear esto. NUNCA commitearlo a git.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # Aplicación
    APP_NAME: str = "Ferretería SaaS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]  # Puerto default de Vite

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "/app/uploads"


# Instancia global — se importa desde cualquier parte del backend
# Se crea una sola vez al arrancar la aplicación
settings = Settings()
