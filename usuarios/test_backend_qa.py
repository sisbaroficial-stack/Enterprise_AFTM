import re

from django.core.management import call_command
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver

from usuarios.models import Usuario


class BackendQASmokeTests(TestCase):
    """
    QA backend de alto nivel:
    - Recorre rutas declaradas en URLConf y valida que no exploten con 500.
    - Ejecuta pruebas con cliente anónimo y autenticado (SUPER_ADMIN).
    - Cubre endpoints críticos de exportación/API.
    """

    @classmethod
    def setUpTestData(cls):
        cls.super_admin = Usuario.objects.create_user(
            username="qa_super_admin",
            password="QaPass12345!",
            email="qa_super_admin@example.com",
            rol="SUPER_ADMIN",
            aprobado=True,
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )

    def _materialize_route(self, route: str) -> str | None:
        # Ignorar patrones regex generados por static/media en DEBUG.
        if "(?P<" in route or route.startswith("^"):
            return None

        replacements = {
            r"<int:[^>]+>": "1",
            r"<slug:[^>]+>": "slug-demo",
            r"<str:[^>]+>": "texto-demo",
            r"<uuid:[^>]+>": "123e4567-e89b-12d3-a456-426614174000",
        }
        concrete = route
        for pattern, value in replacements.items():
            concrete = re.sub(pattern, value, concrete)

        # Si queda un converter desconocido, no se puede materializar de forma segura.
        if "<" in concrete or ">" in concrete:
            return None

        concrete = "/" + concrete.lstrip("/")
        concrete = re.sub(r"/{2,}", "/", concrete)
        return concrete

    def _collect_paths(self):
        paths = []

        def walk(patterns, prefix=""):
            for p in patterns:
                if isinstance(p, URLPattern):
                    route = prefix + str(p.pattern)
                    path = self._materialize_route(route)
                    if not path:
                        continue
                    if path.startswith("/admin/"):
                        continue
                    if path.startswith("/static/") or path.startswith("/media/"):
                        continue
                    paths.append(path)
                elif isinstance(p, URLResolver):
                    walk(p.url_patterns, prefix + str(p.pattern))

        walk(get_resolver().url_patterns)
        # Orden estable y sin duplicados.
        return sorted(set(paths))

    def test_django_check_passes(self):
        call_command("check")

    def test_url_inventory_is_large_enough(self):
        paths = self._collect_paths()
        # Garantiza cobertura amplia del backend.
        self.assertGreaterEqual(len(paths), 70, msg=f"Solo se detectaron {len(paths)} rutas.")

    def test_all_routes_anonymous_no_500(self):
        paths = self._collect_paths()
        failing = []

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, follow=False)
                if response.status_code >= 500:
                    failing.append((path, response.status_code))

        self.assertEqual(
            failing,
            [],
            msg=f"Rutas con error 500 (anónimo): {failing}",
        )

    def test_all_routes_authenticated_superadmin_no_500(self):
        self.client.force_login(self.super_admin)
        paths = self._collect_paths()
        failing = []

        for path in paths:
            # Evita invalidar la sesión en medio del barrido.
            if path.startswith("/usuarios/logout/"):
                continue

            with self.subTest(path=path):
                response = self.client.get(path, follow=False)
                if response.status_code >= 500:
                    failing.append((path, response.status_code))

        self.assertEqual(
            failing,
            [],
            msg=f"Rutas con error 500 (autenticado SUPER_ADMIN): {failing}",
        )

    def test_critical_export_and_api_endpoints(self):
        self.client.force_login(self.super_admin)
        critical_paths = [
            "/reportes/exportar/productos/excel/",
            "/reportes/exportar/movimientos/excel/",
            "/finanzas/exportar/excel/",
            "/finanzas/exportar/pdf/",
            "/compras/exportar/excel/",
            "/compras/exportar/pdf/",
            "/notificaciones/api/recientes/",
        ]

        failing = []
        for path in critical_paths:
            with self.subTest(path=path):
                response = self.client.get(path, follow=False)
                if response.status_code >= 500:
                    failing.append((path, response.status_code))

        self.assertEqual(
            failing,
            [],
            msg=f"Endpoints críticos con 500: {failing}",
        )
