from django import forms
from .models import Task, Sprint, Team

# ==========================================
# 1. Task Form (จัดการงาน)
# ==========================================
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'story_points', 'assignee']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่องาน (Task Title)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'รายละเอียด...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'story_points': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # 🔥 ดึง team_id ที่ส่งมาจาก views.py (ต้องดึงออกก่อนเรียก super)
        team_id = kwargs.pop('team_id', None) 
        super(TaskForm, self).__init__(*args, **kwargs)

        # 🔥 Logic กรองคนรับงาน (Assignee)
        if team_id:
            # กรณีอยู่ในทีม: ให้เลือกได้เฉพาะสมาชิกในทีมนั้น
            try:
                team = Team.objects.get(id=team_id)
                # ดึงเฉพาะ User ที่อยู่ในทีมนี้
                self.fields['assignee'].queryset = team.members.all()
                self.fields['assignee'].empty_label = "--- Unassigned (ยังไม่ระบุคน) ---"
            except Team.DoesNotExist:
                # กันเหนียวเผื่อหาทีมไม่เจอ
                self.fields['assignee'].queryset = team.members.none()
        else:
            # กรณีส่วนตัว: ซ่อนช่อง Assignee ไปเลย (เพราะคืองานของตัวเอง)
            self.fields['assignee'].widget = forms.HiddenInput()


# ==========================================
# 2. Sprint Form (จัดการ Sprint)
# ==========================================
class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ['name', 'goal', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ Sprint (เช่น Sprint 1)'}),
            'goal': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'เป้าหมายของรอบนี้...'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# ==========================================
# 3. Team Form (สร้างทีมใหม่)
# ==========================================
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ตั้งชื่อทีมของคุณ (เช่น Dream Team)'})
        }