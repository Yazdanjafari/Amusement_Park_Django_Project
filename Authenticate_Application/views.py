from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def sign_in(request):
    if request.user.is_authenticated:  # Check if the user is already logged in
        return redirect('Amusement_Park:Products')  # Redirect to the Products page if logged in

    error_message = None  # Initialize error message
    if request.method == "POST":  # Only handle POST requests
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:  # If credentials are correct
            login(request, user)  # Log the user in
            return redirect('Amusement_Park:Products')  # Redirect to the Products page
        else:
            error_message = "نام کاربری یا رمز عبور شما اشتباه است"  # Set error message for invalid credentials

    # Pass the error message to the template
    return render(request, "Authenticate_Application/sign-in.html", {'error_message': error_message})

def logout_show(request):
    logout(request)
    return redirect('Authenticate:Login')  # Redirect to the login page
