from django.urls import path
from . import views

app_name = "Amusement_Park"

urlpatterns = [
    path("Products", views.products, name= "Products"),
    path("Cart", views.cart, name= "Cart"),
    path("Checkout", views.checkout, name= "Checkout"),
    path("Empty-cart", views.empty_cart, name= "Empty-cart"),
    path("Mobile_Error", views.mobile_error, name= "Mobile_Error"),
    path("Refund", views.refund, name= "Refund"),
    path("Setting", views.setting, name= "Setting"),
    path("Submit_Pay", views.submit_pay, name= "Submit_Pay"),
    path("scanner", views.scanner, name= "Scanner"),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
]

