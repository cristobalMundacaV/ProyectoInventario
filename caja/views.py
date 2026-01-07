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
    # Verificar si ya existe caja para hoy
    hoy = timezone.now().date()
    caja_existente = Caja.objects.filter(fecha=hoy).first()
    
    if caja_existente:
        if caja_existente.abierta:
            messages.error(request, 'Ya hay una caja abierta para hoy.')
        else:
            # Reabrir la caja existente
            caja_existente.abierta = True
            caja_existente.hora_apertura = timezone.now()
            caja_existente.save()
            messages.success(request, 'Caja reabierta exitosamente.')
    else:
        # Crear nueva caja si no existe para hoy
        caja = Caja.objects.create(
            fecha=hoy,
            monto_inicial=0,
            hora_apertura=timezone.now()
        )
        messages.success(request, 'Caja abierta exitosamente.')
    
    # Redirigir al home si viene desde allí, sino a caja_list
    next_url = request.GET.get('next', 'home')
    return redirect(next_url)

@login_required
def cerrar_caja(request):
    try:
        caja = Caja.objects.get(abierta=True)
        caja.abierta = False
        caja.hora_cierre = timezone.now()
        caja.save()
        messages.success(request, 'Caja cerrada exitosamente.')
    except Caja.DoesNotExist:
        messages.error(request, 'No hay una caja abierta para cerrar.')
    
    # Redirigir al home si viene desde allí, sino a caja_list
    next_url = request.GET.get('next', 'caja_list')
    return redirect(next_url)
