from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Catégories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Plats
    path('', views.MenuItemListView.as_view(), name='menu_list'),
    path('create/', views.MenuItemCreateView.as_view(), name='menu_create'),
    path('<slug:slug>/', views.MenuItemDetailView.as_view(), name='menu_detail'),
    path('<slug:slug>/update/', views.MenuItemUpdateView.as_view(), name='menu_update'),
    path('<slug:slug>/delete/', views.MenuItemDeleteView.as_view(), name='menu_delete'),
    
    # AJAX
    path('<slug:slug>/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    
    # Menu public (pour serveurs)
    path('public/', views.menu_public, name='menu_public'),
]