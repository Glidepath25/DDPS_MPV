from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'

    def ready(self):
        # Import signal handlers for milestone auto-generation.
        from . import signals  # noqa: F401
