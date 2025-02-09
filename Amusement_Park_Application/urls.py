from django.urls import path
from . import views

app_name = "Amusement_Park"

urlpatterns = [
    path("Products", views.products, name= "Products"),
    path("add_to_cart", views.add_to_cart, name="add_to_cart"),
    path("cancle_cart", views.cancle_cart, name="cancle_cart"),
    path("check_cart", views.check_cart, name="check_cart"),
    path("Cart", views.cart, name= "Cart"),
    path('update_item_quantity/', views.update_item_quantity, name='update_item_quantity'),
    path('calculate-total-price/', views.calculate_total_price, name='calculate_total_price'), 
    path('check-discount-code/', views.check_discount_code, name='check_discount_code'),
    path("Refund", views.refund, name= "Refund"),
    path('get_transaction_details/', views.get_transaction_details, name='get_transaction_details'),
    path('save_refund/', views.save_refund, name='save_refund'),
    path("Setting", views.setting, name= "Setting"),
    path("test_connection", views.test_connection, name= "test_connection"),
    path("test_payment", views.test_payment, name= "test_payment"),
    path("retransaction", views.retransaction, name= "retransaction"),
    path("save_retransaction", views.save_retransaction, name= "save_retransaction"),
    path("submit_pay/", views.submit_pay, name="submit_pay"),
    path("tickets/<int:ticket_id>/print_qr/", views.print_qr, name="print_qr"),
    path("verify_qr_code/", views.verify_qr_code, name="verify_qr_code"),
    path("scanner/", views.scanner, name="Scanner"),
    path('search-customer/', views.search_customer_by_phone, name='search_customer_by_phone'),
    path('save_customer/', views.save_customer, name='save_customer'),
    path("submit_pay", views.submit_pay, name="submit_pay"),
]
