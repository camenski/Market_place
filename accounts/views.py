from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, logout, authenticate

User = get_user_model()


def signup(request):
    if request.method == "POST":
        #Traiter le formulaire
        username = request.POST.get("username")
        password = request.POST.get("password")


        if User.objects.filter(username=username).exists():
            messages.error(request, " Ce nom d'utilisateur existe déjà.")
            return redirect("signup")



        user = User.objects.create_user(username=username,
                                        password=password)
        
        login(request, user)
        messages.success(request, "Inscription réussie ! Bienvenue")
        return redirect('index')

    return render(request, 'accounts/signup.html')


def login_user(request):
    if request.method == "POST":
        # Connecter l'utilisateur
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')

    return render(request, 'accounts/login.html')



def logout_user(request):
    logout(request)
    return redirect('index')
