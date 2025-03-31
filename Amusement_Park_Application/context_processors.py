from django.shortcuts import render
from .models import Notification

def products(request):
    Notification_views = Notification.objects.all()
    
    return {'Notification_views': Notification_views,}