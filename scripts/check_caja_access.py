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
resp = client.get('/')
print('home status', resp.status_code)
resp = client.get('/caja/')
print('caja_list status', resp.status_code)
print('caja_list redirected?', resp.redirect_chain)
print('content length', len(resp.content))
open('scripts/check_caja_response.html','wb').write(resp.content)
print('Saved content to scripts/check_caja_response.html')
