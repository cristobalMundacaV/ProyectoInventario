from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Actividad

@login_required
def auditoria_list(request):
    actividades = Actividad.objects.all().order_by('-fecha_hora')[:100]
    return render(request, 'auditoria/auditoria_list.html', {'actividades': actividades})
