from django.http import HttpResponse
from django.shortcuts import render


def homePage(request):
    user_email = request.session.get('user_email', None)
    return render(request, 'index.html', {'user_email': user_email})

def register(request):
    return render(request,"./register.html")

def login(request):
    return render(request,"./login.html")

def service(request):
    return render(request,"./service.html")

def about(request):
    return render(request,"./about.html")

def contact(request):
    return render(request,"./contact.html")



