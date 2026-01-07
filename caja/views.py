from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Caja

@login_required
def caja_list(request):
    cajas = Caja.objects.all().order_by('-fecha')
    return render(request, 'caja/caja_list.html', {'cajas': cajas})

@login_required
def abrir_caja(request):
    if Caja.objects.filter(abierta=True).exists():
        messages.error(request, 'Ya hay una caja abierta.')
        return redirect('caja_list')
    
    caja = Caja.objects.create(
        fecha=timezone.now().date(),
        monto_inicial=0
    )
    messages.success(request, 'Caja abierta exitosamente.')
    return redirect('caja_list')

@login_required
def cerrar_caja(request):
    try:
        caja = Caja.objects.get(abierta=True)
        caja.abierta = False
        caja.cerrada_por = request.user
        caja.save()
        messages.success(request, 'Caja cerrada exitosamente.')
    except Caja.DoesNotExist:
        messages.error(request, 'No hay una caja abierta para cerrar.')
    return redirect('caja_list')
