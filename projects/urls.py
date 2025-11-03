from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("clients/", views.ClientListView.as_view(), name="client-list"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client-detail"),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path("jobs/create/", views.JobCreateView.as_view(), name="job-create"),
    path("jobs/<int:pk>/", views.JobDetailView.as_view(), name="job-detail"),
    path("jobs/<int:pk>/edit/", views.JobUpdateView.as_view(), name="job-edit"),
    path("exports/jobs/", views.JobExcelExportView.as_view(), name="job-export"),
]
