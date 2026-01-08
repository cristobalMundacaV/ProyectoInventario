from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Checks that /caja/ is accessible and prints response status and a snippet'

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.first()
        if not user:
            self.stdout.write('No users found')
            return
        c = Client()
        c.force_login(user)
        resp = c.get('/caja/')
        self.stdout.write(f'status: {resp.status_code}')
        if resp.status_code == 200:
            self.stdout.write('Page contains table header: ' + ('Total Vendido' in resp.content.decode('utf-8')))
        else:
            self.stdout.write('Redirect chain: ' + str(resp.redirect_chain))
