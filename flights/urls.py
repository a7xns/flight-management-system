from django.urls import path
from . import views


urlpatterns = [
    path('reports/', views.admin_view_reports, name='admin_view_reports'),
    path('add-new-flight/', views.add_new_flight, name='add_new_flight'),
    path('view-flights/', views.view_flights, name='view_flights'),
    path('flight-management/', views.flight_management, name='flight_management'),
    path('delete-flight/<str:flight_id>', views.delete_flight, name='delete_flight'),
    path('search-flight/', views.search_flight, name='search_flight'),
    path('flight_details/<str:flight_id>', views.flight_details, name='flight_details'),
]