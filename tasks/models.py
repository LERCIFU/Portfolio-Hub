from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. Team & Roles (จัดการทีมและสิทธิ์)
# ==========================================
class Team(models.Model):
    name = models.CharField(max_length=100)
    # 🔥 เปลี่ยนมาใช้ through='TeamMember' เพื่อเก็บ Role ของสมาชิก
    members = models.ManyToManyField(User, through='TeamMember', related_name='teams') 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),   # เจ้าของทีม (ทำได้ทุกอย่าง + ลบทีม)
        ('ADMIN', 'Admin'),   # จัดการงาน/คนได้ (ลบทีมไม่ได้)
        ('MEMBER', 'Member'), # ทำงานได้อย่างเดียว
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'team') # ป้องกัน user ซ้ำในทีมเดิม

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"


# ==========================================
# 2. Sprint Model (เหมือนเดิม)
# ==========================================
class Sprint(models.Model):
    name = models.CharField(max_length=100)
    goal = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='created_sprints')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='sprints')

    def __str__(self):
        return self.name


# ==========================================
# 3. Task Model (เพิ่ม Assignee)
# ==========================================
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
    
    # 🔥 เพิ่ม Assignee (คนรับผิดชอบงาน)
    assignee = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tasks'
    )

    # เชื่อมกับ Sprint
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    source = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='tasks')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')

    def __str__(self):
        return self.title