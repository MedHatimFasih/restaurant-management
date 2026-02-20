from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls', namespace='users')),
    path('menu/', include('apps.menu.urls', namespace='menu')),
    path('tables/', include('apps.tables.urls', namespace='tables')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('', include('apps.dashboard.urls', namespace='home')),  # Utilisation d'un namespace unique
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
