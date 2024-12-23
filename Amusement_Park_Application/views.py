from django.shortcuts import render

def products(request):
    return render(request, "Amusement_Park_Application/index.html")
