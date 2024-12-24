from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def sign_in(request):
    if request.user.is_authenticated:  # Check if the user is already logged in
        return redirect('Amusement_Park:Products')  # Use the URL name for redirection

    user = None  # Define `user` outside the POST condition to avoid scope issues
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:  # If credentials are correct
            login(request, user)  # Log the user in
            return redirect('Amusement_Park:Products')  # Redirect to the Products page

    return render(request, "Authenticate_Application/sign-in.html")  # Render login page

def logout_show(request):
    logout(request)
    return redirect('Authenticate:Login')  # Redirect to the login page
