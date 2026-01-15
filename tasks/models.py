from django.db import models
from django.contrib.auth.models import User

# 1. สร้าง Model ทีม (Workspace)
class Team(models.Model):
    name = models.CharField(max_length=100)
    # related_name='teams' เพื่อให้เราเรียก user.teams.all() ได้ใน views
    members = models.ManyToManyField(User, related_name='teams') 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# 2. Model Sprint
class Sprint(models.Model):
    name = models.CharField(max_length=100)
    goal = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 🔥 เพิ่ม 2 บรรทัดนี้ (เพื่อให้รองรับ Views ตัวใหม่)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='created_sprints')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='sprints')

    def __str__(self):
        return self.name

# 3. Model Task
class Task(models.Model):
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    story_points = models.IntegerField(default=1)
    
    # เชื่อมกับ Sprint (ถ้าเป็น Null คือ Backlog)
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    
    source = models.CharField(max_length=100, blank=True, null=True) # เก็บว่ามาจาก Sprint ไหน (ตอนย้าย)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 เพิ่ม 2 บรรทัดนี้เช่นกัน
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='tasks')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')

    def __str__(self):
        return self.title