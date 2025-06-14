from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit
import requests

# def verify_hcaptcha(response_token):
#     secret_key = 'ES_5435bc1566ce4a098e57b2dd11bc60d3'
#     url = 'https://hcaptcha.com/siteverify'
#     data = {
#         'secret': secret_key,
#         'response': response_token,
#     }
#     response = requests.post(url, data=data)
#     result = response.json()
#     print("hCaptcha verification result:", result)  # Debug line
#     return result.get('success', False)

@ratelimit(key='ip', rate='5/10m', method='POST', block=False)
def sign_in(request):
    if request.user.is_authenticated:
        if request.user.role == 'scanner':
            return redirect('Amusement_Park:Scanner')
        return redirect('Amusement_Park:Products')

    error_message = None

    if request.method == "POST":
        if getattr(request, 'limited', False):
            error_message = "تعداد دفعات تلاش ورود شما بیش از حد مجاز است. لطفاً پس از 10 دقیقه مجددا امتحان کنید"
            return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})

        # captcha_response = request.POST.get('h-captcha-response')

        # if not captcha_response:
        #     error_message = "لطفاً کپچا را تکمیل کنید."
        #     return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})

        # if not verify_hcaptcha(captcha_response):
        #     error_message = "کپچا به درستی تکمیل نشده است."
        #     return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.role == 'scanner':
                return redirect('Amusement_Park:Scanner')
            return redirect('Amusement_Park:Products')
        else:
            error_message = "نام کاربری یا رمز عبور شما اشتباه است"

    return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})

def logout_show(request):
    logout(request)
    return redirect('Authenticate:Login')
