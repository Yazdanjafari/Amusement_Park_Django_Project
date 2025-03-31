from django.urls import path
from . import views

app_name = "Authenticate"

urlpatterns = [
    path("", views.sign_in, name="Login"),
    path('logout', views.logout_show, name="Logout"),    
]

