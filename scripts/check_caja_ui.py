import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
print('user:', user.username)
client = Client()
client.force_login(user)
resp = client.get('/caja/')
print('/caja/ status', resp.status_code)
content = resp.content.decode('utf-8')
print('Contains "Cajas" header?', '<h2' in content and 'Cajas' in content)
print('Contains filter form?', 'name="fecha_desde"' in content and 'name="estado"' in content)
open('scripts/caja_page.html','w', encoding='utf-8').write(content)
print('Saved page to scripts/caja_page.html')
