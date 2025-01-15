from django.shortcuts import render
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required


# --------------------------------------------- products --------------------------------------------- #
@login_required
def products(request):
    Product_Views = Product.objects.all()
    
    return render(request, "Amusement_Park_Application/index.html", context={'Product_Views': Product_Views,})

# ---------------------------------------------   --------------------------------------------- #
@login_required
def cart(request):
    return render(request, "Amusement_Park_Application/Cart.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def checkout(request):
    return render(request, "Amusement_Park_Application/Checkout.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def empty_cart(request):
    return render(request, "Amusement_Park_Application/Empty-cart.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def mobile_error(request):
    return render(request, "Amusement_Park_Application/Mobile_Error.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def refund(request):
    return render(request, "Amusement_Park_Application/Refund.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def setting(request):
    return render(request, "Amusement_Park_Application/Setting.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def submit_pay(request):
    return render(request, "Amusement_Park_Application/Submit_Pay.html")

