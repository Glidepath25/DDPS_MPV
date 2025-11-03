from __future__ import annotations

import io
from datetime import date

import pandas as pd
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
    CreateView,
    UpdateView,
)

from accounts.models import User

from .forms import JobAttachmentForm, JobForm, JobNoteForm, MilestoneFormSet, ProjectForm
from .models import Client, Job, JobAttachment, JobAuditLog, JobNote, Milestone, Project
from .services import (
    clients_for_user,
    job_milestones_prefetched,
    jobs_for_user,
    projects_for_user,
)


class InternalAccessRequired(UserPassesTestMixin):
    def test_func(self) -> bool:
        user: User = self.request.user
        return user.is_superuser or user.role in {
            User.Role.INTERNAL,
            User.Role.SIKLA,
        }

    def handle_no_permission(self):
        raise Http404("You do not have permission to perform this action.")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "projects/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user: User = self.request.user
        projects = projects_for_user(user)[:8]
        jobs = (
            jobs_for_user(user)
            .filter(actual_completion__isnull=True)
            .order_by("anticipated_completion")[:10]
        )
        today = timezone.now().date()
        upcoming_milestones = (
            Milestone.objects.filter(job__in=jobs_for_user(user))
            .filter(planned_date__gte=today)
            .select_related("job", "job__project")
            .order_by("planned_date")[:10]
        )
        context.update(
            {
                "projects": projects,
                "jobs": jobs,
                "upcoming_milestones": upcoming_milestones,
            }
        )
        return context


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "projects/client_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        return clients_for_user(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.user.is_authenticated and request.user.is_client_user:
            single_client = queryset.first()
            if single_client:
                return redirect("client-detail", pk=single_client.pk)
        return super().dispatch(request, *args, **kwargs)


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = "projects/client_detail.html"

    def get_queryset(self):
        return clients_for_user(self.request.user).prefetch_related(
            "projects__jobs__milestones", "access_assignments__user"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        context["jobs"] = (
            Job.objects.filter(project__client=client)
            .select_related("project")
            .prefetch_related("milestones")
            .order_by("project__reference", "reference")
        )
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"

    def get_queryset(self):
        return projects_for_user(self.request.user).prefetch_related(
            "jobs__milestones"
        )


class ProjectCreateView(InternalAccessRequired, LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get("client")
        if client_id:
            try:
                initial["client"] = clients_for_user(self.request.user).get(pk=client_id)
            except Client.DoesNotExist:
                pass
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["client"].queryset = clients_for_user(self.request.user)
        return form

    def get_success_url(self):
        messages.success(self.request, "Project created successfully.")
        return reverse("project-detail", kwargs={"pk": self.object.pk})


class JobCreateView(InternalAccessRequired, LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = "projects/job_form.html"

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get("project")
        if project_id:
            try:
                project = projects_for_user(self.request.user).get(pk=project_id)
                initial["project"] = project
            except Project.DoesNotExist:
                pass
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        form.fields["project"].queryset = projects_for_user(user)
        internal_users = User.objects.filter(
            Q(role__in=[User.Role.INTERNAL, User.Role.SIKLA]) | Q(is_superuser=True)
        )
        form.fields["owner"].queryset = internal_users
        form.fields["design_manager"].queryset = internal_users
        form.fields["client_contact"].queryset = User.objects.filter(
            client_assignments__client__in=clients_for_user(user)
        ).distinct()
        if not user.can_view_finance:
            form.fields["actual_revenue"].widget = forms.HiddenInput()
            form.fields["actual_revenue"].required = False
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Job created successfully.")
        return response

    def get_success_url(self):
        return reverse("job-detail", kwargs={"pk": self.object.pk})


class JobUpdateView(InternalAccessRequired, LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = "projects/job_form.html"

    def get_queryset(self):
        return jobs_for_user(self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        form.fields["project"].queryset = projects_for_user(user)
        internal_users = User.objects.filter(
            Q(role__in=[User.Role.INTERNAL, User.Role.SIKLA]) | Q(is_superuser=True)
        )
        form.fields["owner"].queryset = internal_users
        form.fields["design_manager"].queryset = internal_users
        form.fields["client_contact"].queryset = User.objects.filter(
            client_assignments__client__in=clients_for_user(user)
        ).distinct()
        if not user.can_view_finance:
            form.fields["actual_revenue"].widget = forms.HiddenInput()
            form.fields["actual_revenue"].required = False
        return form

    def form_valid(self, form):
        messages.success(self.request, "Job updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("job-detail", kwargs={"pk": self.object.pk})


class JobDetailView(LoginRequiredMixin, DetailView):
    model = Job
    template_name = "projects/job_detail.html"

    def get_queryset(self):
        return job_milestones_prefetched(self.request.user)

    def _user_can_edit(self) -> bool:
        user: User = self.request.user
        return user.is_superuser or user.role in {User.Role.INTERNAL, User.Role.SIKLA}

    def _configure_job_form(self, form: JobForm):
        user = self.request.user
        form.fields["project"].queryset = projects_for_user(user)
        internal_users = User.objects.filter(
            Q(role__in=[User.Role.INTERNAL, User.Role.SIKLA]) | Q(is_superuser=True)
        ).distinct()
        form.fields["owner"].queryset = internal_users
        form.fields["design_manager"].queryset = internal_users
        form.fields["client_contact"].queryset = User.objects.filter(
            client_assignments__client__in=clients_for_user(user)
        ).distinct()
        if not user.can_view_finance:
            form.fields["actual_revenue"].widget = forms.HiddenInput()
            form.fields["actual_revenue"].required = False
        return form

    def _get_job_form(self, data=None, disable=True):
        form = JobForm(data=data, instance=self.object)
        self._configure_job_form(form)
        if disable:
            for field in form.fields.values():
                field.widget.attrs["disabled"] = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "job_form" not in context:
            context["job_form"] = self._get_job_form()
        milestone_formset = context.get("milestone_formset")
        if milestone_formset is None:
            milestone_formset = MilestoneFormSet(instance=self.object)
            context["milestone_formset"] = milestone_formset
        if not self._user_can_edit():
            for form in milestone_formset.forms:
                for field in form.fields.values():
                    field.widget.attrs["disabled"] = True
        if "note_form" not in context:
            context["note_form"] = JobNoteForm()
        if "attachment_form" not in context:
            context["attachment_form"] = JobAttachmentForm()
        context.setdefault("job_form_has_errors", False)
        context.setdefault("milestone_form_errors", False)
        context.setdefault("note_form_errors", False)
        context.setdefault("attachment_form_errors", False)
        context["notes"] = self.object.diary_entries.select_related("author")
        context["attachments"] = self.object.attachments.select_related("uploaded_by")
        context["audit_logs"] = self.object.audit_logs.select_related("actor")
        context["can_edit_job"] = self._user_can_edit()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user

        if "job_update" in request.POST:
            if not self._user_can_edit():
                raise PermissionDenied
            job_form = self._get_job_form(data=request.POST, disable=False)
            if job_form.is_valid():
                old_values = {
                    field: getattr(self.object, field) for field in job_form.fields
                }
                job_form.save()
                self.object.refresh_from_db()
                for field in job_form.changed_data:
                    previous = old_values.get(field)
                    new_value = getattr(self.object, field)
                    if previous != new_value:
                        JobAuditLog.objects.create(
                            job=self.object,
                            actor=user,
                            action="job_field_updated",
                            field_name=field,
                            previous_value=str(previous or ""),
                            new_value=str(new_value or ""),
                        )
                messages.success(request, "Job details updated.")
                return HttpResponseRedirect(self.request.path)
            context = self.get_context_data(
                job_form=job_form,
                job_form_has_errors=True,
            )
            return self.render_to_response(context)

        if "milestone_update" in request.POST:
            if not self._user_can_edit():
                raise PermissionDenied
            formset = MilestoneFormSet(request.POST, instance=self.object)
            if formset.is_valid():
                changes = []
                for form in formset.forms:
                    if not form.cleaned_data or not form.has_changed():
                        continue
                    stage = form.instance.get_stage_display()
                    for field in form.changed_data:
                        previous = form.initial.get(field)
                        new_value = form.cleaned_data.get(field)
                        changes.append((stage, field, previous, new_value))
                formset.save()
                for stage, field, previous, new_value in changes:
                    JobAuditLog.objects.create(
                        job=self.object,
                        actor=user,
                        action="milestone_updated",
                        field_name=f"{stage} - {field}",
                        previous_value=str(previous or ""),
                        new_value=str(new_value or ""),
                    )
                messages.success(request, "Milestones updated.")
                return HttpResponseRedirect(self.request.path)
            context = self.get_context_data(
                milestone_formset=formset,
                milestone_form_errors=True,
            )
            return self.render_to_response(context)

        if "add_note" in request.POST:
            note_form = JobNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.job = self.object
                note.author = user if user.is_authenticated else None
                note.save()
                JobAuditLog.objects.create(
                    job=self.object,
                    actor=user,
                    action="note_added",
                    note=note.body,
                )
                messages.success(request, "Note added to job.")
                return HttpResponseRedirect(self.request.path)
            context = self.get_context_data(
                note_form=note_form,
                note_form_errors=True,
            )
            return self.render_to_response(context)

        if "add_attachment" in request.POST:
            if not self._user_can_edit():
                raise PermissionDenied
            attachment_form = JobAttachmentForm(request.POST, request.FILES or None)
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.job = self.object
                attachment.uploaded_by = user if user.is_authenticated else None
                attachment.save()
                JobAuditLog.objects.create(
                    job=self.object,
                    actor=user,
                    action="attachment_added",
                    field_name=attachment.get_category_display(),
                    new_value=attachment.filename,
                )
                messages.success(request, "Attachment uploaded.")
                return HttpResponseRedirect(self.request.path)
            context = self.get_context_data(
                attachment_form=attachment_form,
                attachment_form_errors=True,
            )
            return self.render_to_response(context)

        return HttpResponseRedirect(self.request.path)


class JobExcelExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        jobs = job_milestones_prefetched(request.user)
        rows = []
        for job in jobs:
            for milestone in job.milestones.all():
                rows.append(
                    {
                        "Project": job.project.reference,
                        "Job": job.reference,
                        "Job Title": job.title,
                        "Job Status": job.get_status_display(),
                        "Stage": milestone.get_stage_display(),
                        "Planned Date": milestone.planned_date,
                        "Actual Date": milestone.actual_date,
                        "Owner": job.owner.get_full_name() if job.owner else "",
                        "Design Manager": job.design_manager.get_full_name()
                        if job.design_manager
                        else "",
                        "Client": job.project.client.name,
                        "Client Contact": job.client_contact.get_full_name()
                        if job.client_contact
                        else "",
                        "Forecast Revenue": job.forecast_revenue,
                        "Actual Revenue": job.actual_revenue if request.user.can_view_finance else None,
                    }
                )
        if not rows:
            rows.append(
                {
                    "Project": "",
                    "Job": "",
                    "Job Title": "",
                    "Job Status": "",
                    "Stage": "",
                    "Planned Date": "",
                    "Actual Date": "",
                    "Owner": "",
                    "Design Manager": "",
                    "Client": "",
                    "Client Contact": "",
                    "Forecast Revenue": 0,
                    "Actual Revenue": 0 if request.user.can_view_finance else None,
                }
            )
        frame = pd.DataFrame(rows)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            frame.to_excel(writer, index=False, sheet_name="Jobs")
        buffer.seek(0)
        filename = f"ddps_jobs_{date.today().isoformat()}.xlsx"
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
