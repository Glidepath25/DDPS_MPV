from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client

from accounts.models import User


class Command(BaseCommand):
    help = (
        "Make anonymous and authenticated requests to '/' with a chosen host "
        "and dump the first part of the response for debugging."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            default=None,
            help="HTTP host header to use (defaults to the first ALLOWED_HOST)",
        )
        parser.add_argument(
            "--username",
            default="sikla.manager",
            help="Username to authenticate with (default: sikla.manager)",
        )
        parser.add_argument(
            "--password",
            default="Demo123!",
            help="Password to authenticate with (default: Demo123!)",
        )

    def _pick_host(self, candidate: str | None) -> str:
        if candidate:
            return candidate
        allowed: Iterable[str] = settings.ALLOWED_HOSTS
        for host in allowed:
            if host not in {"localhost", "127.0.0.1"}:
                return host
        return "localhost"

    def handle(self, *args, **options):
        host = self._pick_host(options.get("host"))
        username: str = options["username"]
        password: str = options["password"]

        client = Client(HTTP_HOST=host)
        resp = client.get("/")
        self.stdout.write(f"Anonymous GET / ({host}) -> {resp.status_code}")
        if resp.status_code >= 400:
            self.stdout.write(resp.content.decode(errors="ignore")[:500])

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
            return

        logged_client = Client(HTTP_HOST=host)
        if not logged_client.login(username=username, password=password):
            self.stdout.write(
                self.style.ERROR(
                    f"Unable to log in as {username} with password {password!r}"
                )
            )
            return

        resp = logged_client.get("/")
        self.stdout.write(f"Logged-in GET / ({host}) -> {resp.status_code}")
        if resp.status_code >= 400:
            self.stdout.write(resp.content.decode(errors="ignore")[:500])
