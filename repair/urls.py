from django.urls import path
from . import views

app_name = 'repair'

urlpatterns = [
    path('', views.index, name='index'),
    path('repairs/', views.repair_list, name='repair_list'),
    path('repairs/<int:repair_id>/', views.repair_detail, name='repair_detail'),
    path('repairs/<int:repair_id>/act/', views.repair_act, name='repair_act'),
    path('clients/', views.client_list, name='client_list'),
    path('components/', views.component_list, name='component_list'),
]

