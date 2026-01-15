from django.contrib import admin
from .models import Task, Sprint, Team

# ลงทะเบียน Model Team (ของใหม่)
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    # 👇 แก้ตรงนี้: เปลี่ยน is_completed เป็น is_active
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'team', 'created_by')
    list_filter = ('is_active', 'team') 
    search_fields = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'sprint', 'team', 'created_by')
    list_filter = ('status', 'priority', 'sprint', 'team')
    search_fields = ('title', 'description')