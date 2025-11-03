from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Client(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    account_code = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128, blank=True)
    country = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="managed_clients",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def revenue_actual(self) -> Decimal:
        return (
            self.projects.aggregate(total=models.Sum("jobs__actual_revenue"))["total"]
            or Decimal("0.00")
        )

    @property
    def revenue_forecast(self) -> Decimal:
        return (
            self.projects.aggregate(total=models.Sum("jobs__forecast_revenue"))["total"]
            or Decimal("0.00")
        )


class ClientAccess(TimeStampedModel):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="access_assignments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_assignments",
    )
    role_title = models.CharField(
        max_length=128, blank=True, help_text="Optional description of the user's role."
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ("client", "user")
        verbose_name = "Client access"
        verbose_name_plural = "Client access"

    def __str__(self) -> str:
        return f"{self.client} -> {self.user}"


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        ACTIVE = "active", "Active"
        HOLD = "hold", "On Hold"
        COMPLETE = "complete", "Complete"

    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="projects"
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNING
    )
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference} - {self.name}"


class Job(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING_REQUIREMENTS = (
            "pending_requirements",
            "Pending requirements",
        )
        REQUIREMENTS_ANALYSIS = (
            "requirements_analysis",
            "Requirements analysis",
        )
        DRAWINGS_WIP = (
            "drawings_wip",
            "Drawings WIP",
        )
        PENDING_CLIENT_APPROVAL = (
            "pending_client_approval",
            "Pending client approval",
        )
        APPROVED_PENDING_FABRICATION = (
            "approved_pending_fabrication",
            "Approved pending fabrication",
        )
        IN_FABRICATION = (
            "in_fabrication",
            "In fabrication",
        )
        IN_QUALITY_CONTROL = (
            "in_quality_control",
            "In quality control",
        )
        READY_TO_BE_SHIPPED = (
            "ready_to_be_shipped",
            "Ready to be shipped",
        )
        SHIPPED = (
            "shipped",
            "Shipped",
        )
        COMPLETED = (
            "completed",
            "Completed",
        )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    reference = models.CharField(max_length=50)
    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.PENDING_REQUIREMENTS,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owned_jobs",
    )
    design_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="managed_design_jobs",
    )
    client_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="client_jobs",
    )
    anticipated_start = models.DateField(blank=True, null=True)
    anticipated_completion = models.DateField(blank=True, null=True)
    actual_completion = models.DateField(blank=True, null=True)
    forecast_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    actual_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["project", "reference"]
        unique_together = ("project", "reference")

    def __str__(self) -> str:
        return f"{self.project.reference}-{self.reference}"

    def current_stage(self) -> str:
        latest = self.milestones.order_by("-actual_date", "-planned_date").first()
        return latest.get_stage_display() if latest else "Not yet scheduled"

    def next_milestone(self):
        today = timezone.now().date()
        return (
            self.milestones.filter(planned_date__gte=today)
            .order_by("planned_date")
            .first()
        )


class Milestone(TimeStampedModel):
    class Stage(models.TextChoices):
        CREATED = "created", "Created"
        REQUIREMENTS_ANALYSIS = "requirements_analysis", "Requirements Analysis"
        DRAWING_COMPLETION = "drawing_completion", "Drawing Completion"
        CLIENT_APPROVAL = "client_approval", "Client Approval"
        FABRICATION = "fabrication", "Fabrication"
        QUALITY_CONTROL = "quality_control", "Quality Control"
        DELIVERY = "delivery", "Delivery"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="milestones")
    stage = models.CharField(max_length=32, choices=Stage.choices)
    planned_date = models.DateField(blank=True, null=True)
    actual_date = models.DateField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["job", "planned_date"]
        unique_together = ("job", "stage")

    def __str__(self) -> str:
        return f"{self.job} - {self.get_stage_display()}"


class JobNote(TimeStampedModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="diary_entries")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_notes",
    )
    body = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        author = self.author.get_full_name() if self.author else "Unknown"
        return f"Note by {author} on {self.created_at:%Y-%m-%d}"


def job_attachment_upload_to(instance: "JobAttachment", filename: str) -> str:
    return f"job_attachments/{instance.job.id}/{filename}"


class JobAttachment(TimeStampedModel):
    class Category(models.TextChoices):
        DRAWING_DRAFT = "drawing_draft", "Drawing - Draft"
        QUOTE = "quote", "Quote"
        DRAWING_APPROVED = "drawing_approved", "Drawing - Approved"
        CLIENT_APPROVAL = "client_approval", "Client Approval"
        DISPATCH_CONFIRMATION = "dispatch_confirmation", "Dispatch Confirmation"
        DELIVERY_CONFIRMATION = "delivery_confirmation", "Delivery Confirmation"
        REQUIREMENTS = "requirements", "Requirements"
        OTHER = "other", "Other"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_attachments",
    )
    category = models.CharField(max_length=64, choices=Category.choices)
    file = models.FileField(upload_to=job_attachment_upload_to)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.job} - {self.get_category_display()}"

    @property
    def filename(self) -> str:
        return self.file.name.split("/")[-1]


class JobAuditLog(TimeStampedModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_audit_entries",
    )
    action = models.CharField(max_length=64)
    field_name = models.CharField(max_length=128, blank=True)
    previous_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        actor = self.actor.get_full_name() if self.actor else "System"
        return f"{self.job} - {self.action} by {actor}"
