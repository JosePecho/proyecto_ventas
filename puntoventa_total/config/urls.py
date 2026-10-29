from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import FileResponse
from config.health import healthz


def service_worker(request):
    respuesta = FileResponse(
        (settings.BASE_DIR / "static/js/offline/service_worker.js").open("rb"),
        content_type="application/javascript",
    )
    respuesta["Cache-Control"] = "no-cache"
    respuesta["Service-Worker-Allowed"] = "/"
    return respuesta

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("service-worker.js", service_worker, name="service_worker"),
    path("admin/", admin.site.urls),
    path("", include("src.modules.identity.presentation.urls")),
    path("catalogo/", include("src.modules.catalog.presentation.urls")),
    path("inventario/", include("src.modules.inventory.presentation.urls")),
    path("pos/", include("src.modules.sales.presentation.urls")),
    path("caja/", include("src.modules.cash_register.presentation.urls")),
    path("pedidos/", include("src.modules.orders.presentation.urls")),
    path("clientes/", include("src.modules.customers.presentation.urls")),
    path("promociones/", include("src.modules.promotions.presentation.urls")),
    path("reportes/", include("src.modules.reporting.presentation.urls")),
    path("auditoria/", include("src.modules.auditing.presentation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
