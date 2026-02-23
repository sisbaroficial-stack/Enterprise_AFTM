from pathlib import Path

# ===================== BASE =====================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['*']
#----------------------------------------------LO DE ARRIBAAGREGUE PARA EL HOSTINGE
# ===================== APPS =====================
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # para humanizar números

    # Apps propias
    'empresas',
    'usuarios',
    'categorias',
    'inventario',
    'movimientos',
    #'dashboard',
    'proveedores',
    'sucursales',
    'facturas',
    'compras',
    'finanzas',
    'notificaciones',
    'horarios',
    'crispy_forms',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# ===================== MIDDLEWARE =====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',                 # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',    # Login / Admin
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware propio
    'sucursales.middleware.SucursalMiddleware',
]

# ===================== URLS =====================
ROOT_URLCONF = 'sisbar_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',        # necesario para login
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sucursales.context_processors.sucursal_actual',
            ],
        },
    },
]

WSGI_APPLICATION = 'sisbar_config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ===================== INTERNACIONALIZACIÓN =====================
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ===================== STATIC =====================
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===================== EMAIL =====================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===================== USUARIO CUSTOM =====================
AUTH_USER_MODEL = 'usuarios.Usuario'



#AGREGUE PARA EL HOSTINGE--------------------------


# Login/Logout URLs
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'usuarios:login'

# Messages Framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Security Settings (para producción)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True



# ===================== DATABASE =====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'AFTM.SAS',
        'USER': 'postgres',
        'PASSWORD': 'Holama.1521',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
