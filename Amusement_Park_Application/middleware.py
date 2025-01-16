from django.shortcuts import reverse
from django.http import HttpResponseRedirect
from user_agents import parse
from django.http import Http404
from django.shortcuts import redirect

class MobileAccessMiddleware:
    """
    Middleware to restrict access to specific pages for mobile users.
    """
    def __init__(self, get_response):
        self.get_response = get_response

        # Pages that mobile users are restricted from accessing
        self.mobile_restricted_pages = [
            'Amusement_Park:Products',
            'Amusement_Park:Cart',
            'Amusement_Park:Checkout',
            'Amusement_Park:Empty-cart',
            'Amusement_Park:Refund',
            'Amusement_Park:Setting',
            'Amusement_Park:Submit_Pay',
        ]
        
        # Pages that mobile users are allowed to access
        self.allowed_paths = [
            reverse('Amusement_Park:Scanner'),  # Scanner page
            reverse('Authenticate:Login'),  # Login page
            reverse('Authenticate:Logout'),  # Logout page
        ]        

        # Page to redirect mobile users when accessing restricted pages
        self.error_page = 'Amusement_Park:Mobile_Error'

    def __call__(self, request):
        user_agent = parse(request.META.get('HTTP_USER_AGENT', ''))
        current_path = request.path

        # Check if the request comes from a mobile device
        is_mobile = user_agent.is_mobile


        if is_mobile:
            # Redirect if the current path is a restricted page
            for restricted_page in self.mobile_restricted_pages:
                if current_path == reverse(restricted_page):
                    return HttpResponseRedirect(reverse(self.error_page))

        return self.get_response(request)




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