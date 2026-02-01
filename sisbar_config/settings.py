from pathlib import Path

# ===================== BASE =====================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

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
    'usuarios',
    'categorias',
    'inventario',
    'movimientos',
    #'dashboard',
    'proveedores',
    'sucursales',

    # Librerías externas
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

# ===================== DATABASE =====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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





LOGIN_URL = 'usuarios:login'  # SIN barra inicial
LOGIN_REDIRECT_URL = 'dashboard:home'  # ✅ BIEN - Con comillas
LOGOUT_REDIRECT_URL = 'index'  # Redirige al index principal