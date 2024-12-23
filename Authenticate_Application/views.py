from django.shortcuts import render

def sign_in(request):
    return render(request, "Authenticate_Application/sign-in.html")



