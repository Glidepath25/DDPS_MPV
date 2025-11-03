from django.core.management.base import BaseCommand
from django.test import Client

from accounts.models import User


class Command(BaseCommand):
    help = "Diagnose responses for anonymous and Sikla_Tony users"

    def handle(self, *args, **options):
        client = Client()
        resp = client.get('/')
        self.stdout.write(f"Anonymous GET / -> {resp.status_code}")
        if resp.status_code >= 400:
            self.stdout.write(resp.content.decode(errors='ignore')[:500])

        try:
            user = User.objects.get(username='Sikla_Tony')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User Sikla_Tony not found'))
            return

        logged_client = Client()
        if not logged_client.login(username='Sikla_Tony', password='Glidepath25'):
            self.stdout.write(self.style.ERROR('Unable to log in as Sikla_Tony with password Glidepath25'))
            return

        resp = logged_client.get('/')
        self.stdout.write(f"Logged-in GET / -> {resp.status_code}")
        if resp.status_code >= 400:
            self.stdout.write(resp.content.decode(errors='ignore')[:500])
