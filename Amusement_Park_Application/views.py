from django.shortcuts import render, redirect
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json

# --------------------------------------------- products --------------------------------------------- #

def products(request):
    Product_Views = Product.objects.all()  # Ensure data is returned here
    # Fetch cart items from the session
    cart = request.session.get('cart', [])
    cart_items = []

    for item in cart:
        product = get_object_or_404(Product, id=item['product_id'])
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
        })

    return render(request, "Amusement_Park_Application/index.html", {
        'Product_Views': Product_Views,  # Ensure this variable is passed
        'cart': cart_items,
    })


def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity')

        # Get the cart from session
        cart = request.session.get('cart', [])

        # Check if the product is already in the cart
        existing_item = next((item for item in cart if item['product_id'] == product_id), None)
        if existing_item:
            existing_item['quantity'] += quantity  # Update quantity if the product is already in the cart
        else:
            cart.append({'product_id': product_id, 'quantity': quantity})  # Add new item to cart

        # Save the cart back to session
        request.session['cart'] = cart

        # Fetch the cart items to return the updated list
        cart_items = []
        for item in cart:
            product = get_object_or_404(Product, id=item['product_id'])
            cart_items.append({
                'product': {
                    'id': product.id,
                    'title': product.title,
                    'price': product.price,
                    'image_url': product.image.url,
                },
                'quantity': item['quantity'],
            })

        return JsonResponse({'status': 'success', 'cart_items': cart_items})
    
    
    
def cancle_cart(request):
    if request.method == 'POST':
        request.session['cart'] = []  # Clear the cart
        return JsonResponse({'status': 'success', 'message': 'Cart emptied'})  


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

