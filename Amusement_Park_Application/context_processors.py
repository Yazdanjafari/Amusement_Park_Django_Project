from django.shortcuts import render
from .models import Notification

def products(request):
    Notification_views = Notification.objects.all()
    
    return {'Notification_views': Notification_views,}

def check_cart(request):
    cart = request.session.get('cart', [])
    cart_empty = len(cart) == 0
    return JsonResponse({'cart_empty': cart_empty})