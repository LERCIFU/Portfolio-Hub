from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # เปลี่ยนจากหน้า list เดิม เป็นหน้า board
    path('', views.task_board, name='board'),
    path('update/<int:task_id>/<str:new_status>/', views.update_task_status, name='update_status'),
    path('add/', views.add_task, name='add_task'),
    path('add-sprint/', views.add_sprint, name='add_sprint'),
    path('edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('api/move-task/', views.move_task_api, name='move_task_api'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('create-team/', views.create_team, name='create_team'),
    path('team/<int:team_id>/manage/', views.manage_team, name='manage_team'),
    path('team/<int:team_id>/remove/<int:user_id>/', views.remove_team_member, name='remove_team_member'),
    path('start-sprint/<int:sprint_id>/', views.start_sprint, name='start_sprint'),
    path('complete-sprint/<int:sprint_id>/', views.complete_sprint, name='complete_sprint'),
    path('edit-sprint/<int:sprint_id>/', views.edit_sprint, name='edit_sprint'),
    path('delete-sprint/<int:sprint_id>/', views.delete_sprint, name='delete_sprint'),
    path('dashboard/', views.dashboard, name='dashboard'),

]