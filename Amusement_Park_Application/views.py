from django.shortcuts import render


# ---------------------------------------------   --------------------------------------------- #
def products(request):
    return render(request, "Amusement_Park_Application/index.html")
# ---------------------------------------------   --------------------------------------------- #
def cart(request):
    return render(request, "Amusement_Park_Application/Cart.html")
# ---------------------------------------------   --------------------------------------------- #
def checkout(request):
    return render(request, "Amusement_Park_Application/Checkout.html")
# ---------------------------------------------   --------------------------------------------- #
def empty_cart(request):
    return render(request, "Amusement_Park_Application/Empty-cart.html")
# ---------------------------------------------   --------------------------------------------- #
def mobile_error(request):
    return render(request, "Amusement_Park_Application/Mobile_Error.html")
# ---------------------------------------------   --------------------------------------------- #
def refund(request):
    return render(request, "Amusement_Park_Application/Refund.html")
# ---------------------------------------------   --------------------------------------------- #
def setting(request):
    return render(request, "Amusement_Park_Application/Setting.html")
# ---------------------------------------------   --------------------------------------------- #
def submit_pay(request):
    return render(request, "Amusement_Park_Application/Submit_Pay.html")

