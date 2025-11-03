from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from projects.models import Client, ClientAccess, Job, Milestone, Project


class Command(BaseCommand):
    help = "Seed demo data for the DDPS application."

    def handle(self, *args, **options):
        today = timezone.now().date()

        admin, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "System",
                "last_name": "Admin",
                "role": User.Role.INTERNAL,
                "is_staff": True,
                "is_superuser": True,
                "can_view_finance": True,
                "can_view_programme": True,
                "can_view_technical": True,
                "can_view_client_details": True,
            },
        )
        if admin_created:
            admin.set_password("Admin123!")
            admin.save()

        sikla_manager, _ = User.objects.get_or_create(
            username="sikla.manager",
            defaults={
                "email": "manager@sikla-demo.com",
                "first_name": "Sarah",
                "last_name": "McLean",
                "role": User.Role.SIKLA,
                "is_staff": True,
                "can_view_finance": True,
            },
        )
        if not sikla_manager.has_usable_password():
            sikla_manager.set_password("Demo123!")
            sikla_manager.save()

        finance_lead, _ = User.objects.get_or_create(
            username="finance.lead",
            defaults={
                "email": "finance@sikla-demo.com",
                "first_name": "James",
                "last_name": "Ortega",
                "role": User.Role.INTERNAL,
                "is_staff": True,
                "can_view_finance": True,
            },
        )
        if not finance_lead.has_usable_password():
            finance_lead.set_password("Demo123!")
            finance_lead.save()

        client_user, _ = User.objects.get_or_create(
            username="client.jane",
            defaults={
                "email": "jane.doe@harlandsteel.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "role": User.Role.CLIENT,
                "can_view_programme": True,
                "can_view_technical": True,
                "can_view_client_details": True,
            },
        )
        if not client_user.has_usable_password():
            client_user.set_password("Demo123!")
            client_user.save()

        sikla_client, _ = Client.objects.get_or_create(
            account_code="SIKLA",
            defaults={
                "name": "Sikla Industrial",
                "notes": "Internal projects and R&D initiatives.",
            },
        )

        harland_client, _ = Client.objects.get_or_create(
            account_code="HAR001",
            defaults={
                "name": "Harland Steel",
                "address": "100 Foundry Road",
                "city": "Belfast",
                "country": "UK",
                "notes": "Key pipe support client for energy sector.",
                "account_manager": sikla_manager,
            },
        )

        ClientAccess.objects.get_or_create(
            client=harland_client,
            user=client_user,
            defaults={"role_title": "Client Engineering Lead", "is_primary": True},
        )

        project_alpha, _ = Project.objects.get_or_create(
            reference="HP-2401",
            defaults={
                "name": "Harland Pipe Racks",
                "client": harland_client,
                "status": Project.Status.ACTIVE,
                "description": "Design and supply of modular pipe rack supports for the Harland energy expansion.",
                "start_date": today - timedelta(days=45),
            },
        )

        job_main, created = Job.objects.get_or_create(
            project=project_alpha,
            reference="JOB-001",
            defaults={
                "title": "Main process line supports",
                "owner": sikla_manager,
                "design_manager": finance_lead,
                "client_contact": client_user,
                "anticipated_start": today - timedelta(days=30),
                "anticipated_completion": today + timedelta(days=15),
                "forecast_revenue": Decimal("125000"),
                "actual_revenue": Decimal("82000"),
                "notes": "Phase 1 fabrication in progress.",
                "status": Job.Status.IN_FABRICATION,
            },
        )

        if created:
            milestone_plan = {
                Milestone.Stage.CREATED: (today - timedelta(days=45), today - timedelta(days=44)),
                Milestone.Stage.REQUIREMENTS_ANALYSIS: (today - timedelta(days=35), today - timedelta(days=33)),
                Milestone.Stage.DRAWING_COMPLETION: (today - timedelta(days=10), today - timedelta(days=8)),
                Milestone.Stage.CLIENT_APPROVAL: (today - timedelta(days=5), today - timedelta(days=4)),
                Milestone.Stage.FABRICATION: (today, None),
                Milestone.Stage.QUALITY_CONTROL: (today + timedelta(days=10), None),
                Milestone.Stage.DELIVERY: (today + timedelta(days=21), None),
            }
            for stage, (planned, actual) in milestone_plan.items():
                milestone = job_main.milestones.get(stage=stage)
                milestone.planned_date = planned
                milestone.actual_date = actual
                milestone.save()

        job_secondary, created = Job.objects.get_or_create(
            project=project_alpha,
            reference="JOB-002",
            defaults={
                "title": "Ancillary steam line supports",
                "owner": finance_lead,
                "design_manager": sikla_manager,
                "client_contact": client_user,
                "anticipated_start": today - timedelta(days=10),
                "anticipated_completion": today + timedelta(days=40),
                "forecast_revenue": Decimal("54000"),
                "notes": "Awaiting final client comments on revision B drawings.",
                "status": Job.Status.DRAWINGS_WIP,
            },
        )

        if created:
            plan = {
                Milestone.Stage.CREATED: (today - timedelta(days=12), today - timedelta(days=12)),
                Milestone.Stage.REQUIREMENTS_ANALYSIS: (today - timedelta(days=8), today - timedelta(days=7)),
                Milestone.Stage.DRAWING_COMPLETION: (today + timedelta(days=3), None),
                Milestone.Stage.CLIENT_APPROVAL: (today + timedelta(days=10), None),
                Milestone.Stage.FABRICATION: (today + timedelta(days=21), None),
                Milestone.Stage.QUALITY_CONTROL: (today + timedelta(days=32), None),
                Milestone.Stage.DELIVERY: (today + timedelta(days=45), None),
            }
            for stage, (planned, actual) in plan.items():
                milestone = job_secondary.milestones.get(stage=stage)
                milestone.planned_date = planned
                milestone.actual_date = actual
                milestone.save()

        project_internal, _ = Project.objects.get_or_create(
            reference="RD-9901",
            defaults={
                "name": "Sikla tooling refresh",
                "client": sikla_client,
                "status": Project.Status.PLANNING,
                "description": "Internal initiative to modernise tooling for quick-turn bracket production.",
            },
        )

        Job.objects.get_or_create(
            project=project_internal,
            reference="INT-001",
            defaults={
                "title": "Bracket automation pilot",
                "owner": sikla_manager,
                "design_manager": sikla_manager,
                "forecast_revenue": Decimal("0"),
                "notes": "Internal R&D job.",
                "status": Job.Status.PENDING_REQUIREMENTS,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(
            "Log in with admin/Admin123! or sikla.manager/Demo123! for internal access."
        )
        self.stdout.write(
            "Client portal demo: client.jane / Demo123! (only sees Harland Steel)."
        )

