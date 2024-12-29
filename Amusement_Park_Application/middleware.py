from django.shortcuts import reverse
from django.http import HttpResponseRedirect
from user_agents import parse

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
