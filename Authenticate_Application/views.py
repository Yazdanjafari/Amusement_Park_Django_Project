from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/10m', method='POST', block=False)
def sign_in(request):
    if request.user.is_authenticated:
        if request.user.role == 'scanner':
            return redirect('Amusement_Park:Scanner')  # Redirect scanner users
        return redirect('Amusement_Park:Products')  # Redirect other users

    error_message = None

    if request.method == "POST":
        if getattr(request, 'limited', False):
            error_message = "تعداد دفعات تلاش ورود شما بیش از حد مجاز است. لطفاً پس از 10 دقیقه مجددا امتحان کنید."
            return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.role == 'scanner':
                return redirect('Amusement_Park:Scanner')  # Redirect scanner users
            return redirect('Amusement_Park:Products')  # Redirect other users
        else:
            error_message = "نام کاربری یا رمز عبور شما اشتباه است"

    return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})


def logout_show(request):
    logout(request)
    return redirect('Authenticate:Login')  # Redirect to the login page
