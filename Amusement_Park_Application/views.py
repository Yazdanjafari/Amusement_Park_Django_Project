from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

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
        return JsonResponse({'status': 'success',})  


def check_cart(request):
    cart = request.session.get('cart', [])
    cart_empty = len(cart) == 0
    return JsonResponse({'cart_empty': cart_empty})


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

    cart_empty = len(cart_items) == 0

    return render(request, "Amusement_Park_Application/Cart.html", {
        'cart_items': cart_items,
        'get_TaxRate': get_TaxRate,
        'cart_empty': cart_empty,
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
            return JsonResponse({'success': False,})

        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        birth_year = request.POST.get('birthYear')
        birth_month = request.POST.get('birthMonth')
        birth_day = request.POST.get('birthDay')

        try:
            date_of_birth = f"{birth_year}-{birth_month}-{birth_day}"
        except Exception as e:
            return JsonResponse({'success': False,})

        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'first_purchase': timezone.now(),
                'last_purchase': timezone.now(),
            }
        )

        if not created:
            customer.last_purchase = timezone.now()
            customer.save()

        return JsonResponse({'success': True, 'message': 'اطلاعات کاربر با موفقیت ذخیره شد.', 'customer_id': customer.id})
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است.'})
 
    
    
@csrf_exempt
def create_ticket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        cart_items = data.get('cart_items')

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'مشتری یافت نشد.'})

        ticket = Ticket.objects.create(
            customer=customer,
            user=request.user,
            is_scanned=False,
            desc='توضیحات بلیت'
        )

        for item in cart_items:
            product = Product.objects.get(id=item['product_id'])
            TicketProduct.objects.create(
                ticket=ticket,
                product=product,
                quantity=item['quantity']
            )

        return JsonResponse({'success': True, 'message': 'بلیت با موفقیت ایجاد شد.', 'ticket_id': ticket.id})
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است.'})    
    

@csrf_exempt
def create_transaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')
        transaction_type = data.get('transaction_type')
        discount_code = data.get('discount_code')
        discount_amount = data.get('discount_amount')
        mix_pc = data.get('mix_pc')
        mix_cash = data.get('mix_cash')

        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'بلیت یافت نشد.'})

        offer = None
        if discount_code:
            offer = Offer.objects.filter(code=discount_code, activate=True).first()

        transaction = Transaction.objects.create(
            user=request.user,
            ticket=ticket,
            type=transaction_type,
            mix_pc=mix_pc,
            mix_cash=mix_cash,
            offer=offer,
            discount=discount_amount,
            product_prices=ticket.total_price(),
            tax=ticket.calculate_tax(),
            price=ticket.calculate_final_price(),
            desc='توضیحات تراکنش'
        )

        return JsonResponse({'success': True, 'message': 'تراکنش با موفقیت ایجاد شد.', 'transaction_id': transaction.id})
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است.'})


@csrf_exempt
def submit_pay(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")

            customer_data = data.get('customer_data')
            cart_items = data.get('cart_items')
            transaction_data = data.get('transaction_data')

            transaction_type = transaction_data.get('type', 'pc')
            mix_pc = transaction_data.get('mix_pc')
            mix_cash = transaction_data.get('mix_cash')

            if transaction_type == 'mix' and (mix_pc is None or mix_cash is None):
                return JsonResponse({'success': False, 'message': 'برای تراکنش ترکیبی، مقادیر نقدی و کارتخوان باید پر شوند.'})

            customer = None
            if customer_data:
                customer, created = Customer.objects.get_or_create(
                    phone=customer_data['phone'],
                    defaults={
                        'first_name': customer_data.get('firstName', ''),
                        'last_name': customer_data.get('lastName', ''),
                        'date_of_birth': f"{customer_data.get('birthYear')}-{customer_data.get('birthMonth')}-{customer_data.get('birthDay')}",
                        'first_purchase': timezone.now(),
                        'last_purchase': timezone.now(),
                    }
                )

            ticket = Ticket.objects.create(
                customer=customer, 
                user=request.user,
                is_scanned=False,
                desc='توضیحات بلیت'
            )

            for item in cart_items:
                product = Product.objects.get(id=item['product_id'])
                TicketProduct.objects.create(
                    ticket=ticket,
                    product=product,
                    quantity=item['quantity']
                )

            total_price = sum(item.product.price * item.quantity for item in ticket.ticket_products.all())

            tax_rate = TaxRate.objects.first().rate  
            tax = int(total_price * tax_rate / 100)

            final_price = total_price + tax

            offer = None
            discount_amount = 0  # Initialize discount_amount to 0

            if transaction_data.get('discount_code'):
                offer = Offer.objects.filter(code=transaction_data['discount_code'], activate=True).first()
                if offer:
                    discount_amount = int(final_price * offer.persent / 100)
            else:
                # Only apply manual_discount if no offer is applied
                discount_amount = transaction_data.get('discount_amount', 0)

            final_price -= discount_amount

            transaction = Transaction.objects.create(
                user=request.user,
                ticket=ticket,
                type=transaction_type,
                mix_pc=mix_pc,
                mix_cash=mix_cash,
                offer=offer, 
                manual_discount=0 if offer else discount_amount,  # Set manual_discount to 0 if offer exists
                product_prices=total_price,
                tax=tax,
                price=final_price,
                desc=None
            )

            return JsonResponse({'success': True, 'message': 'پرداخت با موفقیت انجام شد.'})

        except Exception as e:
            logger.error(f"Error in submit_pay: {str(e)}")  
            return JsonResponse({'success': False, 'message': f'خطا در پرداخت: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است.'})



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

# --------------------------------------------- retransaction page (Submit_pay.html) --------------------------------------------- #

@login_required
def retransaction(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        transaction_id = request.POST.get('transaction_id')
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            now = timezone.now()
            time_difference = now - transaction.create_at

            if time_difference > timedelta(hours=24):
                return JsonResponse({
                    'status': 'error',
                    'message': 'سیستم قادر نیست این تراکنش را مجددا ثبت کند زیرا این تراکنش بیشتر از یک روز پیش ثبت شده و ممکن است تخفیف ها ، مالیات و قیمت های آن زمان و الان متفاوت باشد'
                })
            else:
                ticket_products = TicketProduct.objects.filter(ticket=transaction.ticket)
                customer = transaction.ticket.customer

                products = []
                for ticket_product in ticket_products:
                    products.append({
                        'image': ticket_product.product.image.url,
                        'title': ticket_product.product.title,
                        'quantity': ticket_product.quantity,
                        'price': ticket_product.product.price
                    })

                return JsonResponse({
                    'status': 'success',
                    'data': {
                        'id': transaction.id,
                        'create_at': transaction.create_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_prices': transaction.product_prices,
                        'tax': transaction.tax,
                        'discount': transaction.discount,
                        'price': transaction.price,
                        'customer': {
                            'first_name': customer.first_name if customer else 'N/A',
                            'last_name': customer.last_name if customer else 'N/A',
                            'phone': customer.phone if customer else 'N/A'
                        },
                        'products': products
                    }
                })
        except Transaction.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'خریدی با این کد پیگیری یافت نشد'
            })
    return render(request, "Amusement_Park_Application/Submit_Pay.html")


@csrf_exempt
def save_retransaction(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            transaction_id = data.get("transaction_id")
            transaction_type = data.get("transaction_type", "pc")
            mix_pc = data.get("mix_pc")
            mix_cash = data.get("mix_cash")
            desc = data.get("desc")
            
            mix_pc = int(mix_pc) if mix_pc and str(mix_pc).strip() != "" else None
            mix_cash = int(mix_cash) if mix_cash and str(mix_cash).strip() != "" else None
            
            try:
                original_transaction = Transaction.objects.get(id=transaction_id)
            except Transaction.DoesNotExist:
                return JsonResponse({"status": "error", "message": "تراکنش مورد نظر یافت نشد."})
            
            rerecording = RerecordingTransaction(
                rerecording_transaction=original_transaction,
                type=transaction_type,
                mix_pc=mix_pc,
                mix_cash=mix_cash,
                user=request.user,
                is_success=True,  
                desc=desc,
            )
            
            rerecording.full_clean()
            
            rerecording.save()
            
            return JsonResponse({"status": "success", "message": "فروش مجدد با موفقیت ثبت شد."})
        
        except ValidationError as ve:
            return JsonResponse({"status": "error", "message": ve.message_dict})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    
    return JsonResponse({"status": "error", "message": "متد درخواست صحیح نیست."})




# ---------------------------------------------   --------------------------------------------- #
@login_required
def scanner(request):
    if request.user.role == 'kiosk':
        raise Http404("Page not found")  # User with KIOSK role gets a 404 error
    return render(request, "Amusement_Park_Application/scanner.html")
