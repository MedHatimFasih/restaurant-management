from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Tableau de bord principal
    path('', views.home, name='home'),
    
    # Rapports et statistiques
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/menu/', views.menu_performance, name='menu_performance'),
    path('reports/staff/', views.staff_performance, name='staff_performance'),
    
    # Alertes système
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/<int:pk>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Journal d'activité
    path('logs/', views.ActivityLogListView.as_view(), name='activity_log'),
    
    # Export de données
    path('export/sales/csv/', views.export_sales_csv, name='export_sales_csv'),
    
    # API pour graphiques (AJAX)
    path('api/charts/revenue/', views.chart_revenue_api, name='chart_revenue_api'),
    path('api/charts/orders/', views.chart_orders_api, name='chart_orders_api'),
]
