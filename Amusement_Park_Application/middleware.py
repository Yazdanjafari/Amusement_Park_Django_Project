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
    
    
    

class RoleBasedAccessMiddleware: #For scanner accounts
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow unrestricted access to login page
        allowed_paths = [
            reverse('Amusement_Park:Scanner'),  # Scanner page
            reverse('Authenticate:Login'),  # Login page
            reverse('Authenticate:Logout'),  # Logout page
        ]

        # Restrict SCANNER users
        if request.user.is_authenticated and request.user.role == 'scanner':
            if request.path not in allowed_paths:
                return redirect('Amusement_Park:Scanner')  # Redirect to scanner page

        return self.get_response(request)    
    
    
    
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