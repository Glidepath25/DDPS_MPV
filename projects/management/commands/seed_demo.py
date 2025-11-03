from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from django.db import transaction

from accounts.models import User
from projects.models import Client, ClientAccess, Job, JobAttachment, JobAuditLog, JobNote, Milestone, Project


class Command(BaseCommand):
    help = "Seed demo data for the DDPS application."

    def handle(self, *args, **options):
        today = timezone.now().date()

        with transaction.atomic():
            # Clear previous demo content while keeping core accounts.
            JobAttachment.objects.all().delete()
            JobNote.objects.all().delete()
            JobAuditLog.objects.all().delete()
            Milestone.objects.all().delete()
            Job.objects.all().delete()
            Project.objects.all().delete()
            ClientAccess.objects.all().delete()
            Client.objects.all().delete()

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

        clients_info = [
            ("CLT001", "Jones"),
            ("CLT002", "Kirby"),
            ("CLT003", "Designer Group"),
            ("CLT004", "BMD"),
            ("CLT005", "MSL"),
        ]

        clients = {}
        for code, name in clients_info:
            clients[name] = Client.objects.create(
                account_code=code,
                name=name,
                address=f"{name} HQ",
                city="London",
                country="UK",
                notes=f"Preferred partner: {name}.",
                account_manager=sikla_manager,
            )
            ClientAccess.objects.create(
                client=clients[name],
                user=sikla_manager,
                role_title="Portfolio Lead",
                is_primary=True,
            )

        project_specs = [
            {
                "name": "Novonordisk",
                "reference": "NOVO-001",
                "client": clients["Jones"],
                "status": Project.Status.ACTIVE,
                "description": "Pipe support delivery for new insulin production facility.",
                "start_delta": -90,
                "end_delta": 90,
            },
            {
                "name": "Sanofi",
                "reference": "SAN-002",
                "client": clients["Kirby"],
                "status": Project.Status.ACTIVE,
                "description": "Expansion of biologics plant utility corridors.",
                "start_delta": -60,
                "end_delta": 60,
            },
            {
                "name": "Amgen",
                "reference": "AMG-003",
                "client": clients["Designer Group"],
                "status": Project.Status.HOLD,
                "description": "Process piping retrofit feasibility.",
                "start_delta": -30,
                "end_delta": 120,
            },
            {
                "name": "BMS",
                "reference": "BMS-004",
                "client": clients["BMD"],
                "status": Project.Status.ACTIVE,
                "description": "Modular rooftop support frames across packaging lines.",
                "start_delta": -75,
                "end_delta": 45,
            },
            {
                "name": "MSD",
                "reference": "MSD-005",
                "client": clients["MSL"],
                "status": Project.Status.PLANNING,
                "description": "Greenfield riser installation study.",
                "start_delta": -15,
                "end_delta": 150,
            },
        ]

        job_status_sequence = [
            Job.Status.IN_FABRICATION,
            Job.Status.APPROVED_PENDING_FABRICATION,
            Job.Status.DRAWINGS_WIP,
            Job.Status.PENDING_CLIENT_APPROVAL,
            Job.Status.COMPLETED,
        ]

        stage_progress_map = {
            Job.Status.PENDING_REQUIREMENTS: Milestone.Stage.CREATED,
            Job.Status.REQUIREMENTS_ANALYSIS: Milestone.Stage.REQUIREMENTS_ANALYSIS,
            Job.Status.DRAWINGS_WIP: Milestone.Stage.DRAWING_COMPLETION,
            Job.Status.PENDING_CLIENT_APPROVAL: Milestone.Stage.CLIENT_APPROVAL,
            Job.Status.APPROVED_PENDING_FABRICATION: Milestone.Stage.CLIENT_APPROVAL,
            Job.Status.IN_FABRICATION: Milestone.Stage.FABRICATION,
            Job.Status.IN_QUALITY_CONTROL: Milestone.Stage.QUALITY_CONTROL,
            Job.Status.READY_TO_BE_SHIPPED: Milestone.Stage.QUALITY_CONTROL,
            Job.Status.SHIPPED: Milestone.Stage.DELIVERY,
            Job.Status.COMPLETED: Milestone.Stage.DELIVERY,
        }

        def set_milestones(job: Job, status: str, base_offset: int):
            stage_order = [
                Milestone.Stage.CREATED,
                Milestone.Stage.REQUIREMENTS_ANALYSIS,
                Milestone.Stage.DRAWING_COMPLETION,
                Milestone.Stage.CLIENT_APPROVAL,
                Milestone.Stage.FABRICATION,
                Milestone.Stage.QUALITY_CONTROL,
                Milestone.Stage.DELIVERY,
            ]
            completed_stage = stage_progress_map.get(status, Milestone.Stage.CREATED)
            planned_start = today + timedelta(days=base_offset)
            for index, milestone in enumerate(
                job.milestones.order_by("created_at")
            ):
                bump = index * 10
                milestone.planned_date = planned_start + timedelta(days=bump)
                if stage_order[index] == completed_stage or stage_order.index(
                    stage_order[index]
                ) < stage_order.index(completed_stage):
                    milestone.actual_date = milestone.planned_date
                else:
                    milestone.actual_date = None
                milestone.save()

        job_names = [
            ("Pipe run", Decimal("95000"), Decimal("65000")),
            ("Process pipe", Decimal("82000"), Decimal("54000")),
            ("Plant room", Decimal("120000"), Decimal("35000")),
            ("Rooftop", Decimal("67000"), Decimal("0")),
            ("Riser", Decimal("145000"), Decimal("140000")),
        ]

        for idx, spec in enumerate(project_specs, start=1):
            project = Project.objects.create(
                reference=spec["reference"],
                name=spec["name"],
                client=spec["client"],
                status=spec["status"],
                description=spec["description"],
                start_date=today + timedelta(days=spec["start_delta"]),
                end_date=today + timedelta(days=spec["end_delta"]),
            )

            for job_idx, (title, forecast, actual) in enumerate(job_names, start=1):
                status = job_status_sequence[(job_idx - 1) % len(job_status_sequence)]
                job = Job.objects.create(
                    project=project,
                    reference=f"{project.reference}-J{job_idx:02d}",
                    title=title,
                    owner=sikla_manager,
                    design_manager=finance_lead,
                    client_contact=client_user,
                    anticipated_start=today + timedelta(days=(idx * -5 + job_idx * 3)),
                    anticipated_completion=today
                    + timedelta(days=idx * 15 + job_idx * 7),
                    actual_completion=(
                        today + timedelta(days=idx * 10 + job_idx * 6)
                        if status in {Job.Status.COMPLETED, Job.Status.SHIPPED}
                        else None
                    ),
                    forecast_revenue=forecast + Decimal(idx * 5000),
                    actual_revenue=(
                        actual + Decimal(idx * 3000) if actual else Decimal("0")
                    ),
                    notes=f"{title} package for {project.name}.",
                    status=status,
                )
                set_milestones(job, status, base_offset=idx * -20 + job_idx * 5)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(
            "Log in with admin/Admin123! or sikla.manager/Demo123! for internal access."
        )
        self.stdout.write(
            "Client portal demo: client.jane / Demo123! (only sees Harland Steel)."
        )

