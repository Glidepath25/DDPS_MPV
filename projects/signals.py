from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Job, Milestone


@receiver(post_save, sender=Job)
def ensure_milestones_exist(sender, instance: Job, created: bool, **kwargs):
    if not created:
        return
    existing_stages = set(
        instance.milestones.values_list("stage", flat=True)
    )
    for stage, _ in Milestone.Stage.choices:
        if stage not in existing_stages:
            Milestone.objects.create(job=instance, stage=stage)
