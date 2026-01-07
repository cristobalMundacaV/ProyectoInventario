from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Caja
from .forms import AperturaCajaForm

@login_required
def caja_list(request):
    cajas = Caja.objects.all().order_by('-fecha')
    return render(request, 'caja/caja_list.html', {'cajas': cajas})

@login_required
def abrir_caja(request):
    if request.method == 'POST':
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            monto_inicial = form.cleaned_data['monto_inicial']
            caja = Caja.objects.create(
                fecha=timezone.now().date(),
                monto_inicial=monto_inicial,
                hora_apertura=timezone.now(),
                abierta_por=request.user
            )
            messages.success(request, f'Caja abierta exitosamente con monto inicial de ${monto_inicial}.')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = AperturaCajaForm()
    
    return render(request, 'caja/apertura_caja.html', {'form': form})

@login_required
def cerrar_caja(request):
    cajas_abiertas = Caja.objects.filter(abierta=True)
    
    if cajas_abiertas.exists():
        # Cerrar todas las cajas abiertas
        count = cajas_abiertas.count()
        for caja in cajas_abiertas:
            caja.abierta = False
            caja.hora_cierre = timezone.now()
            caja.cerrada_por = request.user
            caja.save()
        
        if count == 1:
            messages.success(request, 'Caja cerrada exitosamente.')
        else:
            messages.success(request, f'Se cerraron {count} cajas exitosamente.')
    else:
        messages.error(request, 'No hay cajas abiertas para cerrar.')
    
    # Redirigir al home si viene desde allí, sino a caja_list
    next_url = request.GET.get('next', 'caja_list')
    return redirect(next_url)
