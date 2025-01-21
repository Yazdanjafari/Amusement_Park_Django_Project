from django.urls import path
from . import views

app_name = "Amusement_Park"

urlpatterns = [
    path("Products", views.products, name= "Products"),
    path("add_to_cart", views.add_to_cart, name="add_to_cart"),
    path("cancle_cart", views.cancle_cart, name="cancle_cart"),
    path("Cart", views.cart, name= "Cart"),
    path('remove-item-from-cart/', views.remove_item_from_cart, name='remove_item_from_cart'),
    path('update_item_quantity/', views.update_item_quantity, name='update_item_quantity'),
    path('calculate-total-price/', views.calculate_total_price, name='calculate_total_price'), 
    path('check-discount-code/', views.check_discount_code, name='check_discount_code'),
    path("Empty-cart", views.empty_cart, name= "Empty-cart"),
    path("Checkout", views.checkout, name= "Checkout"),
    path("Mobile_Error", views.mobile_error, name= "Mobile_Error"),
    path("Refund", views.refund, name= "Refund"),
    path("Setting", views.setting, name= "Setting"),
    path("Submit_Pay", views.submit_pay, name= "Submit_Pay"),
    path("scanner", views.scanner, name= "Scanner"),
]
