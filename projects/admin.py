from django.contrib import admin

from .models import (
    Client,
    ClientAccess,
    Job,
    JobAttachment,
    JobAuditLog,
    JobNote,
    Milestone,
    Project,
)


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "account_code", "account_manager", "created_at")
    search_fields = ("name", "account_code")
    list_filter = ("account_manager",)


@admin.register(ClientAccess)
class ClientAccessAdmin(admin.ModelAdmin):
    list_display = ("client", "user", "role_title", "is_primary")
    list_filter = ("client", "is_primary")
    search_fields = ("client__name", "user__username", "user__email")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("reference", "name", "client", "status", "start_date", "end_date")
    list_filter = ("status", "client")
    search_fields = ("reference", "name")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "reference",
        "title",
        "status",
        "owner",
        "design_manager",
        "client_contact",
        "forecast_revenue",
        "actual_revenue",
    )
    search_fields = ("reference", "title", "project__reference")
    list_filter = ("project__client", "status")
    inlines = [MilestoneInline]


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("job", "stage", "planned_date", "actual_date")
    list_filter = ("stage", "planned_date")
    search_fields = ("job__reference", "job__project__reference")


@admin.register(JobNote)
class JobNoteAdmin(admin.ModelAdmin):
    list_display = ("job", "author", "created_at")
    search_fields = ("job__reference", "author__username", "body")
    autocomplete_fields = ("job", "author")


@admin.register(JobAttachment)
class JobAttachmentAdmin(admin.ModelAdmin):
    list_display = ("job", "category", "uploaded_by", "created_at")
    list_filter = ("category",)
    search_fields = ("job__reference", "uploaded_by__username", "description")
    autocomplete_fields = ("job", "uploaded_by")


@admin.register(JobAuditLog)
class JobAuditLogAdmin(admin.ModelAdmin):
    list_display = ("job", "action", "field_name", "actor", "created_at")
    list_filter = ("action", "field_name")
    search_fields = ("job__reference", "actor__username", "note")
    autocomplete_fields = ("job", "actor")
