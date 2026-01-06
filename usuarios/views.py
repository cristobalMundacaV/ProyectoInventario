from django.contrib.auth import logout
def logout_view(request):
	logout(request)
	return redirect('login')
from django.shortcuts import redirect
def root_redirect(request):
	return redirect('login')
from django.contrib.auth.decorators import login_required
@login_required
def inicio(request):
	return render(request, 'inicio.html')
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

def login_view(request):
	if request.method == 'POST':
		usuario = request.POST.get('usuario')
		contraseña = request.POST.get('contraseña')
		user = authenticate(request, username=usuario, password=contraseña)
		if user is not None:
			login(request, user)
			return redirect('inicio')  # Cambia 'inicio' por la vista principal si es necesario
		else:
			messages.error(request, 'Usuario o contraseña incorrectos.')
	return render(request, 'login.html')
