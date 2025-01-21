from django.shortcuts import render, redirect
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from decimal import Decimal

# --------------------------------------------- index.html page --------------------------------------------- #

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
        quantity = data.get('quantity', 1)  # Default to 1 if quantity is missing

        cart = request.session.get('cart', [])

        # Check if the product is already in the cart
        existing_item = next((item for item in cart if item['product_id'] == product_id), None)
        if existing_item:
            existing_item['quantity'] = quantity  # Update to the provided quantity
        else:
            cart.append({'product_id': product_id, 'quantity': quantity})

        request.session['cart'] = cart

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


# --------------------------------------------- Cart.html Page --------------------------------------------- #
@login_required
def cart(request):
    get_TaxRate = TaxRate.objects.first()
    cart = request.session.get('cart', [])
    cart_items = []

    for item in cart:
        product = get_object_or_404(Product, id=item['product_id'])
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
        })

    return render(request, "Amusement_Park_Application/Cart.html", {
        'cart_items': cart_items,
        'get_TaxRate': get_TaxRate,
    })

@login_required
def remove_item_from_cart(request):
    if request.method == 'POST':
        # Parse the incoming JSON data
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            # Get the current cart from the session
            cart = request.session.get('cart', [])
            
            # Remove the product with the specified product_id
            cart = [item for item in cart if item['product_id'] != product_id]
            
            # Update the session with the new cart
            request.session['cart'] = cart
            
            # Check if the cart is empty
            cart_empty = len(cart) == 0
            
            return JsonResponse({
                'success': True,
                'cart_empty': cart_empty,
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
def update_item_quantity(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        new_quantity = data.get('quantity')

        # Get the current cart from session
        cart = request.session.get('cart', [])

        # Find the item in the cart and update its quantity
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = new_quantity
                break

        # Update the session with the new cart
        request.session['cart'] = cart

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


@login_required
def calculate_total_price(request):
    get_TaxRate = TaxRate.objects.first().rate  # Assuming get_TaxRate is already a Decimal
    if request.method == 'GET':
        cart = request.session.get('cart', [])
        total_price = Decimal(0)  # Initialize total_price as Decimal

        for item in cart:
            product = get_object_or_404(Product, id=item['product_id'])
            total_price += Decimal(product.price) * Decimal(item['quantity'])  # Convert to Decimal

        total_tax = (total_price / Decimal(100)) * get_TaxRate  # Ensure all operands are Decimal
        tax = int(total_tax)  # Convert tax to integer
        
        return JsonResponse({
            'total_price': int(total_price),  # Convert to int (number)
            'tax': tax,  # Return tax as integer
        })

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
