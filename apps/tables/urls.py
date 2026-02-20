from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    # Tables
    path('', views.TableListView.as_view(), name='table_list'),
    path('<int:pk>/', views.TableDetailView.as_view(), name='table_detail'),
    path('create/', views.TableCreateView.as_view(), name='table_create'),
    path('<int:pk>/update/', views.TableUpdateView.as_view(), name='table_update'),
    path('<int:pk>/delete/', views.TableDeleteView.as_view(), name='table_delete'),
    
    # Plan de salle
    path('floor-plan/', views.floor_plan, name='floor_plan'),
    path('<int:pk>/change-status/', views.change_table_status, name='change_status'),
    path('<int:pk>/toggle-status/', views.toggle_table_status, name='toggle_status'),
    
    # Fusion de tables
    path('merges/', views.TableMergeListView.as_view(), name='merge_list'),
    path('merges/create/', views.TableMergeCreateView.as_view(), name='merge_create'),
    path('merges/<int:pk>/deactivate/', views.deactivate_merge, name='merge_deactivate'),
    
    # Réservations
    path('reservations/', views.ReservationListView.as_view(), name='reservation_list'),
    path('reservations/<int:pk>/', views.ReservationDetailView.as_view(), name='reservation_detail'),
    path('reservations/create/', views.ReservationCreateView.as_view(), name='reservation_create'),
    path('reservations/<int:pk>/update/', views.ReservationUpdateView.as_view(), name='reservation_update'),
    path('reservations/<int:pk>/confirm/', views.confirm_reservation, name='reservation_confirm'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation, name='reservation_cancel'),
    path('reservations/calendar/', views.calendar_view, name='calendar'),
]