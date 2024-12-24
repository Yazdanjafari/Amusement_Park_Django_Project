from django.urls import path
from . import views

app_name = "Amusement_Park"

urlpatterns = [
    path("Products", views.products, name= "Products"),
]

