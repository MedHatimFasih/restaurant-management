from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Liste et gestion des commandes
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/add-items/', views.order_add_items, name='order_add_items'),
    path('<int:pk>/confirm/', views.confirm_order, name='confirm_order'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Gestion des articles (AJAX)
    path('<int:pk>/add-item/', views.add_item_to_order, name='add_item_to_order'),
    path('<int:pk>/remove-item/<int:item_id>/', views.remove_item_from_order, name='remove_item_from_order'),
    path('<int:pk>/update-quantity/<int:item_id>/', views.update_item_quantity, name='update_item_quantity'),
    
    # Remises
    path('<int:pk>/apply-discount/', views.apply_discount, name='apply_discount'),
    
    # Interface cuisine
    path('kitchen/', views.kitchen_display, name='kitchen_display'),
    path('<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Facturation
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('<int:order_pk>/create-invoice/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
]