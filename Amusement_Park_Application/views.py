from django.shortcuts import render
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

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
        
        
@login_required
def check_discount_code(request):
    if request.method == 'GET':
        discount_code = request.GET.get('code', '').strip().lower()  # Get and normalize the discount code
        offer = Offer.objects.filter(code=discount_code, activate=True).first()  # Check if the code exists and is active

        if offer:
            return JsonResponse({
                'success': True,
                'percent': offer.persent,
                'message': f'کد تخفیف {offer.code} با موفقیت اعمال شد.',
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'کد تخفیف وارد شده معتبر نیست.',
            })        
            
            
@login_required
def search_customer_by_phone(request):
    phone = request.GET.get('phone')
    try:
        customer = Customer.objects.get(phone=phone)
        data = {
            'exists': True,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'date_of_birth': customer.date_of_birth.strftime('%Y-%m-%d') if customer.date_of_birth else None,
        }
    except Customer.DoesNotExist:
        data = {
            'exists': False,
        }
    return JsonResponse(data)

@csrf_exempt
def save_customer(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if not phone:
            return JsonResponse({'success': False, 'message': 'شماره تلفن نمی‌تواند خالی باشد.'})

        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        birth_year = request.POST.get('birthYear')
        birth_month = request.POST.get('birthMonth')
        birth_day = request.POST.get('birthDay')

        if Customer.objects.filter(phone=phone).exists():
            return JsonResponse({'success': False, 'message': 'اطلاعات قابل تغییر نیست.'})

        try:
            date_of_birth = f"{birth_year}-{birth_month}-{birth_day}"
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'فرمت تاریخ تولد نامعتبر است.'})

        try:
            customer = Customer(
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                first_purchase=timezone.now(),
                last_purchase=timezone.now(),
            )
            customer.full_clean()
            customer.save()
            return JsonResponse({'success': True, 'message': 'اطلاعات کاربر با موفقیت ذخیره شد.'})
        except ValidationError as e:
            return JsonResponse({'success': False, 'message': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'مشکلی در ذخیره اطلاعات به وجود آمد: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است.'})
 
            

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
