from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='cart.index'),
    path('<int:id>/add/', views.add, name='cart.add'),
    path('clear/', views.clear, name='cart.clear'),
    path('purchase/', views.purchase, name='cart.purchase'),
    path('trending/', views.trending_map, name='cart.trending'),
    path('trending/<str:region_id>/', views.region_top_movies, name='cart.region_top_movies'),
]