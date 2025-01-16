from django.shortcuts import render, redirect
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required
from django.http import Http404

# --------------------------------------------- products --------------------------------------------- #
@login_required
def products(request):
    Product_Views = Product.objects.all()

    # Retrieve cart from session
    cart_items = request.session.get('cart_items', [])

    # Add the cart items to the context
    return render(request, "Amusement_Park_Application/index.html", context={'Product_Views': Product_Views, 'cart_items': cart_items})

def add_to_cart(request, product_id):
    # Get the product from the database
    product = Product.objects.get(id=product_id)

    # Retrieve the cart from session or initialize it
    cart_items = request.session.get('cart_items', [])

    # Check if the product is already in the cart
    for item in cart_items:
        if item['id'] == product.id:
            item['quantity'] += 1
            break
    else:
        cart_items.append({
            'id': product.id,
            'title': product.title,
            'image': product.image.url,
            'price': product.price,
            'quantity': 1
        })

    # Save the updated cart back to the session
    request.session['cart_items'] = cart_items

    return redirect('Amusement_Park:products')
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
    if request.user.role == 'kiosk':
        raise Http404("Page not found")  # User with KIOSK role gets a 404 error
    return render(request, "Amusement_Park_Application/refund.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def setting(request):
    if request.user.role == 'kiosk':
        raise Http404("Page not found")  # User with KIOSK role gets a 404 error
    return render(request, "Amusement_Park_Application/setting.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def submit_pay(request):
    return render(request, "Amusement_Park_Application/Submit_Pay.html")

# ---------------------------------------------   --------------------------------------------- #
@login_required
def scanner(request):
    if request.user.role == 'kiosk':
        raise Http404("Page not found")  # User with KIOSK role gets a 404 error
    return render(request, "Amusement_Park_Application/scanner.html")

