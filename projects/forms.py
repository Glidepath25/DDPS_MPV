from django import forms
from django.forms import inlineformset_factory

from .models import Job, Milestone, Project, JobNote, JobAttachment


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "reference",
            "client",
            "description",
            "status",
            "start_date",
            "end_date",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "project",
            "title",
            "reference",
            "status",
            "owner",
            "design_manager",
            "client_contact",
            "anticipated_start",
            "anticipated_completion",
            "actual_completion",
            "forecast_revenue",
            "actual_revenue",
            "notes",
        ]
        widgets = {
            "anticipated_start": forms.DateInput(attrs={"type": "date"}),
            "anticipated_completion": forms.DateInput(attrs={"type": "date"}),
            "actual_completion": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        project = cleaned.get("project")
        client_contact = cleaned.get("client_contact")
        if project and client_contact:
            if not client_contact.client_assignments.filter(client=project.client).exists():
                self.add_error(
                    "client_contact",
                    "Selected contact is not assigned to this client.",
                )
        return cleaned


class JobNoteForm(forms.ModelForm):
    class Meta:
        model = JobNote
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add an update or diary note..."}
            )
        }


class JobAttachmentForm(forms.ModelForm):
    class Meta:
        model = JobAttachment
        fields = ["category", "description", "file"]
        widgets = {
            "description": forms.TextInput(
                attrs={"placeholder": "Optional description"}
            )
        }


MilestoneFormSet = inlineformset_factory(
    parent_model=Job,
    model=Milestone,
    fields=["stage", "planned_date", "actual_date", "notes"],
    extra=0,
    can_delete=False,
    widgets={
        "planned_date": forms.DateInput(attrs={"type": "date"}),
        "actual_date": forms.DateInput(attrs={"type": "date"}),
        "stage": forms.HiddenInput(),
        "notes": forms.TextInput(),
    },
)
