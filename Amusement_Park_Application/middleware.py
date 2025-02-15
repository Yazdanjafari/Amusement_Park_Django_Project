from django.shortcuts import reverse
from django.http import Http404
from django.shortcuts import redirect

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is trying to access the admin panel
        if request.path.startswith('/admin/'):
            if not request.user.is_superuser:
                raise Http404("Page not found")
        
        response = self.get_response(request)
        return response
    

    
class KioskBasedAccessMiddleware: #For Kiosk accounts
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of pages to restrict for KIOSK users
        restricted_paths_for_kiosk = [
            reverse('Amusement_Park:Refund'),
            reverse('Amusement_Park:Setting'),
            reverse('Amusement_Park:Scanner')
        ]

        # If the user is authenticated and has the 'kiosk' role
        if request.user.is_authenticated and request.user.role == 'kiosk':
            if request.path in restricted_paths_for_kiosk:
                raise Http404("Page not found")  # Return 404 error for restricted pages

        # Default behavior: Allow access
        return self.get_response(request)    


class ScannerBasedAccessMiddleware: #For scanner accounts
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of pages to restrict for scanner users
        restricted_paths_for_scanner = [
            reverse('Amusement_Park:Refund'),
            reverse('Amusement_Park:Setting'),
            reverse('Amusement_Park:Cart'),
            reverse('Amusement_Park:retransaction'),
        ]

        # If the user is authenticated and has the 'scanner' role
        if request.user.is_authenticated and request.user.role == 'scanner':
            if request.path in restricted_paths_for_scanner:
                raise Http404("Page not found")  # Return 404 error for restricted pages

        # Default behavior: Allow access
        return self.get_response(request)    