from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
import logging
import requests
from io import BytesIO
import json, qrcode, base64

logger = logging.getLogger(__name__)

# --------------------------------------------- Having 3 languages --------------------------------------------- #

def switch_language(request, lang_code):
    if lang_code not in ('fa', 'en', 'ar'):
        lang_code = 'fa'

    request.session['language'] = lang_code

    next_url = (
        request.GET.get('next') or
        request.META.get('HTTP_REFERER', '/')
    )

    from urllib.parse import urlparse
    path = urlparse(next_url).path

    for code in ('fa', 'en', 'ar'):
        if path.startswith(f"/{code}/"):
            path = path[len(code)+1:] or '/'

    return redirect(f"/{lang_code}{path}")


# --------------------------------------------- index.html page --------------------------------------------- #

@login_required
def products(request, lang=None):
    sale_mode = request.GET.get('sale_mode')
    if not sale_mode:
        return redirect(f"{request.path}?sale_mode=normal")  # Force default sale_mode

    language = request.session.get('language', 'fa')
    
    if sale_mode == 'tourist':
        Product_Views = Product.objects.filter(product_type=Product.ProductType.tourist)
    else:
        Product_Views = Product.objects.filter(product_type=Product.ProductType.normal)

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
        'Product_Views': Product_Views,
        'cart': cart_items,
        'language': language,
    })


@csrf_exempt
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
    
    
@csrf_exempt    
def cancle_cart(request):
    if request.method == 'POST':
        request.session['cart'] = []  # Clear the cart
        return JsonResponse({'status': 'success',})  

@csrf_exempt
def check_cart(request):
    cart = request.session.get('cart', [])
    cart_empty = len(cart) == 0
    return JsonResponse({'cart_empty': cart_empty})


# --------------------------------------------- Cart.html Page --------------------------------------------- #
@login_required
def cart(request, lang=None):
    language = request.session.get('language', 'fa')
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
        'language': language,
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
            'gender': customer.gender,
            'city': customer.city,
            'country': customer.country,
            
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
        gender = request.POST.get('gender')
        city = request.POST.get('city')
        country = request.POST.get('country')
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
                'gender': gender,
                'city': city,
                'country': country,
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
                desc='توضیحات بلیت'
            )

            for item in cart_items:
                product = Product.objects.get(id=item['product_id'])
                TicketProduct.objects.create(
                    ticket=ticket,
                    product=product,
                    quantity=item['quantity']
                )

            total_price = sum(tp.product.price * tp.quantity for tp in ticket.ticket_products.all())

            tax_rate = TaxRate.objects.first().rate  
            tax = int(total_price * tax_rate / 100)
            final_price = total_price + tax

            offer = None
            discount_amount = 0
            if transaction_data.get('discount_code'):
                offer = Offer.objects.filter(code=transaction_data['discount_code'], activate=True).first()
                if offer:
                    discount_amount = int(final_price * offer.persent / 100)
            else:
                discount_amount = transaction_data.get('discount_amount', 0)
            final_price -= discount_amount

            transaction = Transaction.objects.create(
                user=request.user,
                ticket=ticket,
                type=transaction_type,
                mix_pc=mix_pc,
                mix_cash=mix_cash,
                offer=offer, 
                manual_discount=0 if offer else discount_amount,
                product_prices=total_price,
                tax=tax,
                price=final_price,
                desc=None
            )

            return JsonResponse({'success': True, 'message': 'پرداخت با موفقیت انجام شد.', 'ticket_id': ticket.id})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'خطا در پرداخت: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر است.'})


# --------------------------------------------- refund.html --------------------------------------------- #
@login_required
def refund(request, lang=None):
    language = request.session.get('language', 'fa')
    if request.user.role == 'kiosk':
        raise Http404("Page not found")  
    return render(request, "Amusement_Park_Application/Refund.html", {'language': language,})


@login_required
def get_transaction_details(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        transaction_id = request.GET.get('transaction_id')

        if not transaction_id or not transaction_id.isdigit():
            return JsonResponse({'error': 'شناسه تراکنش نامعتبر است'}, status=400)

        try:
            transaction = Transaction.objects.get(id=int(transaction_id))
            if not transaction.is_success:
                return JsonResponse({'error': 'این فروش وجود ندارد یا منقضی شده است'}, status=404)
        except Transaction.DoesNotExist:
            return JsonResponse({'error': 'این فروش وجود ندارد یا منقضی شده است'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'شناسه تراکنش باید عدد باشد'}, status=400)

        data = {
            'product_prices': transaction.product_prices,
            'tax': transaction.tax,
            'discount': transaction.discount,
            'price': transaction.price,
            'products': []
        }

        for ticket_product in transaction.ticket.ticket_products.all():
            product = ticket_product.product
            image_url = product.image.url if hasattr(product, 'image') and product.image else ''
            data['products'].append({
                'name': product.title,
                'quantity': ticket_product.quantity,
                'price': product.price,
                'total_price': ticket_product.get_total_price(),
                'image': image_url,
            })

        return JsonResponse(data)

    return JsonResponse({'error': 'درخواست نامعتبر'}, status=400)



@login_required
def save_refund(request):
    if request.method == 'POST':
        try:
            transaction_id = request.POST.get('transaction_id')
            refund_type = request.POST.get('refund_type')
            desc = request.POST.get('desc', '')
            source_card_holder_name = request.POST.get('source_card_holder_name', '')
            destination_card_holder_name = request.POST.get('destination_card_holder_name', '')
            source_card_number = request.POST.get('source_card_number', '')
            destination_card_number = request.POST.get('destination_card_number', '')
            source_sheba_number = request.POST.get('source_sheba_number', '')
            destination_sheba_number = request.POST.get('destination_sheba_number', '')

            transaction = get_object_or_404(Transaction, id=transaction_id)
            user = request.user

            returned_transaction = ReturnedTransaction(
                transaction=transaction,
                type=refund_type,
                user=user,
                desc=desc,
                source_card_holder_name=source_card_holder_name,
                destination_card_holder_name=destination_card_holder_name,
                source_card_number=source_card_number,
                destination_card_number=destination_card_number,
                source_sheba_number=source_sheba_number,
                destination_sheba_number=destination_sheba_number
            )
            returned_transaction.save()
            

            return JsonResponse({'status': 'success', 'message': 'عودت وجه با موفقیت ثبت شد.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'}, status=400)



# --------------------------------------------- Setting.html and Bank --------------------------------------------- #

@login_required
def setting(request, lang=None):
    language = request.session.get('language', 'fa')
    if request.user.role == 'kiosk':
        raise Http404("Page not found")
    return render(request, "Amusement_Park_Application/Setting.html", {'language': language,})

@csrf_exempt  
def test_connection(request):
    if request.method == "POST":
        ip = request.POST.get('ip')
        port = request.POST.get('port')
        try:
            url = f"http://{ip}:{port}/api/test"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return JsonResponse({'status': 'success', 'message': 'ارتباط برقرار است'})
            else:
                return JsonResponse({'status': 'error', 'message': 'ارتباط برقرار نیست'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'ارتباط برقرار نیست'})
    return JsonResponse({'status': 'error', 'message': 'روش درخواست نامعتبر است'})

@csrf_exempt
def test_payment(request):
    if request.method == "POST":
        payment = request.POST.get('payment')
        ip = request.POST.get('ip')
        port = request.POST.get('port')
        try:
            payment_value = int(payment)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'مبلغ پرداخت نامعتبر است'})
        try:
            url = f"http://{ip}:{port}/api/payment"
            response = requests.post(url, data={'amount': payment_value}, timeout=5)
            if response.status_code == 200:
                return JsonResponse({'status': 'success', 'message': 'پرداخت با موفقیت انجام شد'})
            else:
                return JsonResponse({'status': 'error', 'message': 'پرداخت ناموفق بود'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'ارتباط برقرار نیست'})
    return JsonResponse({'status': 'error', 'message': 'روش درخواست نامعتبر است'})



# --------------------------------------------- retransaction page (Submit_pay.html) --------------------------------------------- #

@login_required
def retransaction(request, lang=None):
    if request.user.role == 'kiosk' :
        raise Http404("Page not found")
        
    language = request.session.get('language', 'fa')
    
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
    return render(request, "Amusement_Park_Application/Submit_Pay.html", {'language': language,})


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
            
            new_transaction = rerecording.rerecording_transaction
            ticket_id = new_transaction.ticket.id
            
            return JsonResponse({
                "status": "success", 
                "message": "فروش مجدد با موفقیت ثبت شد.",
                "ticket_id": ticket_id,
            })
        
        except ValidationError as ve:
            return JsonResponse({"status": "error", "message": ve.message_dict})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    
    return JsonResponse({"status": "error", "message": "متد درخواست صحیح نیست."})





# --------------------------------------------- QR-Code & Scan --------------------------------------------- #
@login_required
def print_qr(request, ticket_id, lang=None):
    language = request.session.get('language', 'fa')
    ticket = get_object_or_404(Ticket, id=ticket_id)
    transaction = Transaction.objects.filter(ticket=ticket).first()    

    ordered_products = ticket.ticket_products.select_related('product')  # ✅ Get products with their details

    qr_content = {
        "ticket_id": ticket.id,
        "products": [
            {
                "ticket_product_id": tp.id,
                "product_id": tp.product.id,
                "title": tp.product.title,
            }
            for tp in ordered_products
        ]
    }
    qr_json = json.dumps(qr_content)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_json)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('ascii')
    qr_code_image = "data:image/png;base64," + img_str

    return render(request, "Amusement_Park_Application/print_qr.html", {
        "ticket": ticket,
        "qr_code_image": qr_code_image,
        "transaction_id": transaction.id if transaction else None,
        "language": language,
        "ordered_products": ordered_products,  # ✅ Send to template
    })



@csrf_exempt
def verify_qr_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            qr_data = data.get("qr_code")
            product_id = data.get("product_id")
            if not qr_data or not product_id:
                return JsonResponse({"status": "error", "message": "اطلاعات مورد نیاز موجود نیست."})
            try:
                qr_content = json.loads(qr_data)
            except Exception as e:
                return JsonResponse({"status": "error", "message": "داده‌های کیو آر کد نامعتبر است."})
            ticket_id = qr_content.get("ticket_id")
            if not ticket_id:
                return JsonResponse({"status": "error", "message": "کد بلیت موجود نیست."})
            ticket = Ticket.objects.get(id=ticket_id)
            try:
                ticket_product = ticket.ticket_products.get(product__id=product_id)
            except TicketProduct.DoesNotExist:
                return JsonResponse({"status": "error", "message": "❌ این بلیت یافت نشد ❌"})
            if ticket_product.scanned:
                return JsonResponse({"status": "error", "message": "⛔ این بلیت منقضی شده است ⛔"})

            ticket_product.scanned = True
            ticket_product.save()
            return JsonResponse({"status": "success", "message": "✅ بلیت با موفقیت یافت شد ✅"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": "خطایی رخ داده است."})
    return JsonResponse({"status": "error", "message": "درخواست نامعتبر است."})


@login_required
def scanner(request, lang=None):
    language = request.session.get('language', 'fa')     
    products = Product.objects.all()
    return render(request, "Amusement_Park_Application/scanner.html", {"products": products, 'language': language,})