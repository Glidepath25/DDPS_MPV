from __future__ import annotations

from typing import Iterable

from django.db.models import Prefetch, QuerySet, Sum

from accounts.models import User

from .models import Client, Job, Milestone, Project


def clients_for_user(user: User) -> QuerySet[Client]:
    if user.is_superuser or user.role in {User.Role.INTERNAL, User.Role.SIKLA}:
        return Client.objects.all()
    return Client.objects.filter(access_assignments__user=user).distinct()


def projects_for_user(user: User) -> QuerySet[Project]:
    if user.is_superuser or user.role in {User.Role.INTERNAL, User.Role.SIKLA}:
        return Project.objects.select_related("client")
    client_ids = clients_for_user(user).values_list("id", flat=True)
    return Project.objects.filter(client_id__in=client_ids).select_related("client")


def jobs_for_user(user: User) -> QuerySet[Job]:
    qs = Job.objects.select_related(
        "project__client", "owner", "design_manager", "client_contact"
    )
    if user.is_superuser or user.role in {User.Role.INTERNAL, User.Role.SIKLA}:
        return qs
    client_ids = clients_for_user(user).values_list("id", flat=True)
    return qs.filter(project__client_id__in=client_ids)


def job_milestones_prefetched(user: User) -> QuerySet[Job]:
    return jobs_for_user(user).prefetch_related(
        Prefetch("milestones", queryset=Milestone.objects.order_by("planned_date"))
    )


def client_summary_data(client: Client) -> dict[str, Iterable]:
    jobs = (
        client.jobs.select_related("project")
        .prefetch_related("milestones")
        .annotate(
            forecast_total=Sum("forecast_revenue"),
            actual_total=Sum("actual_revenue"),
        )
    )
    return {
        "jobs": jobs,
        "actual_revenue": client.revenue_actual,
        "forecast_revenue": client.revenue_forecast,
    }
