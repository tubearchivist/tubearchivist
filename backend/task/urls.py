"""all tasks api URLs"""

from django.urls import path
from task import views

urlpatterns = [
    path(
        "by-name/",
        views.TaskListView.as_view(),
        name="api-task-list",
    ),
    path(
        "by-name/<slug:task_name>/",
        views.TaskNameListView.as_view(),
        name="api-task-name-list",
    ),
    path(
        "by-id/<slug:task_id>/",
        views.TaskIDView.as_view(),
        name="api-task-id",
    ),
    path(
        "schedule/",
        views.ScheduleListView.as_view(),
        name="api-schedule-list",
    ),
    path(
        "schedule/<slug:task_name>/",
        views.ScheduleView.as_view(),
        name="api-schedule",
    ),
    path(
        "notification/",
        views.ScheduleNotification.as_view(),
        name="api-schedule-notification",
    ),
]
