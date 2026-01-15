from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Task, Sprint, Team
from .forms import TaskForm, SprintForm

# ==========================================
# 1. Main Board (หน้ากระดานงาน)
# ==========================================
@login_required
def task_board(request):
    # --- A. เตรียมข้อมูล Context (Workspace) ---
    my_teams = getattr(request.user, 'teams', None)
    if my_teams:
        my_teams = my_teams.all()
    else:
        my_teams = []

    # รับค่า team_id จาก URL
    current_team_id = request.GET.get('team_id')
    current_team = None
    sprint_queryset = Sprint.objects.none()

    if current_team_id:
        # [โหมดทีม]
        current_team = get_object_or_404(Team, id=current_team_id, members=request.user)
        sprint_queryset = Sprint.objects.filter(team=current_team)
    else:
        # [โหมดส่วนตัว]
        sprint_queryset = Sprint.objects.filter(created_by=request.user, team__isnull=True)

    all_sprints = sprint_queryset.order_by('-id')

    # --- B. Active Sprint ---
    sprint_id = request.GET.get('sprint')
    active_sprint = None

    if sprint_id:
        active_sprint = all_sprints.filter(pk=sprint_id).first()
    else:
        active_sprint = all_sprints.filter(is_active=True).first()

    # --- C. Tasks List ---
    tasks_todo = []
    tasks_in_progress = []
    tasks_done = []

    if active_sprint:
        tasks = active_sprint.tasks.all()
        tasks_todo = tasks.filter(status='TODO')
        tasks_in_progress = tasks.filter(status='IN_PROGRESS')
        tasks_done = tasks.filter(status='DONE')

    # --- D. Backlog Items ---
    if current_team:
        backlog_tasks = Task.objects.filter(sprint__isnull=True, team=current_team)
    else:
        backlog_tasks = Task.objects.filter(sprint__isnull=True, team__isnull=True, created_by=request.user)

    context = {
        'my_teams': my_teams,
        'current_team': current_team,
        'active_sprint': active_sprint,
        'all_sprints': all_sprints,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_done': tasks_done,
        'backlog_tasks': backlog_tasks,
    }
    return render(request, 'tasks/list.html', context)


# ==========================================
# 2. Add Functions (Create)
# ==========================================
@login_required
def add_task(request):
    # 1. รับ team_id (จาก Hidden Input หรือ URL)
    team_id = request.POST.get('team_id') or request.GET.get('team_id')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user 
            
            # 🔥 2. ระบุว่า Task นี้เป็นของทีมไหน (ถ้ามี)
            if team_id:
                target_team = get_object_or_404(Team, id=team_id)
                task.team = target_team
            else:
                task.team = None

            # 🔥 3. Auto-Assign: หา Active Sprint ให้ถูกบริบท!
            # (ถ้าอยู่ทีม ต้องหา Sprint ทีม / ถ้าอยู่ส่วนตัว หา Sprint ส่วนตัว)
            active_sprint_query = Sprint.objects.filter(is_active=True)
            
            if team_id:
                # หา Sprint ที่ Active ของ "ทีมนี้"
                active_sprint = active_sprint_query.filter(team_id=team_id).first()
            else:
                # หา Sprint ที่ Active ของ "ฉัน" (แบบส่วนตัว)
                active_sprint = active_sprint_query.filter(created_by=request.user, team__isnull=True).first()

            if active_sprint:
                task.sprint = active_sprint
            
            task.save()
            
            # 4. Redirect กลับไปถูกห้อง
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            else:
                return redirect('tasks:board')
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Add New Task'})


@login_required
def add_sprint(request):
    # รับ team_id
    team_id = request.POST.get('team_id') or request.GET.get('team_id')

    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            new_sprint = form.save(commit=False)
            new_sprint.created_by = request.user
            
            # 🔥 1. กำหนด Team
            if team_id:
                target_team = get_object_or_404(Team, id=team_id)
                new_sprint.team = target_team
            else:
                new_sprint.team = None

            # 🔥 2. Logic Active / Close Old Sprint
            if new_sprint.is_active:
                old_sprint_query = Sprint.objects.filter(is_active=True)
                
                if team_id:
                    old_sprint = old_sprint_query.filter(team_id=team_id).first()
                else:
                    old_sprint = old_sprint_query.filter(created_by=request.user, team__isnull=True).first()
                
                if old_sprint:
                    old_sprint.is_active = False
                    old_sprint.save()
                
                new_sprint.save()
                
                # ย้ายงานค้าง
                if old_sprint:
                    unfinished_tasks = old_sprint.tasks.exclude(status='DONE')
                    unfinished_tasks.update(sprint=new_sprint, source=old_sprint.name)
            else:
                new_sprint.save()
                
            # Redirect
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            else:
                return redirect('tasks:board')
    else:
        form = SprintForm()

    return render(request, 'tasks/sprint_form.html', {
        'form': form, 
        'title': '🚀 Start New Sprint',
        'button_text': 'Start Sprint'
    })


# ==========================================
# 3. Edit / Delete Functions
# ==========================================
@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    # เก็บ team_id ไว้ส่งกลับหลังแก้เสร็จ
    team_id = task.team.id if task.team else None

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            return redirect('tasks:board')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {
        'form': form, 
        'title': '✏️ Edit Task', 
        'button_text': 'Save Changes'
    })

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    team_id = task.team.id if task.team else None
    
    task.delete()
    
    if team_id:
        return redirect(f'/tasks/?team_id={team_id}')
    return redirect('tasks:board')


# ==========================================
# 4. Utility / API Functions
# ==========================================
@login_required
def update_task_status(request, task_id, new_status):
    task = get_object_or_404(Task, pk=task_id)
    valid_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
    if new_status in valid_statuses:
        task.status = new_status
        task.save()
        
    team_id = task.team.id if task.team else None
    if team_id:
        return redirect(f'/tasks/?team_id={team_id}')
    return redirect('tasks:board')


@csrf_exempt
@login_required
def move_task_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            new_status = data.get('status')
            sprint_id = data.get('sprint_id') 

            task = get_object_or_404(Task, id=task_id)
            task.status = new_status

            if sprint_id:
                task.sprint_id = sprint_id 
            else:
                task.sprint = None  

            task.save()
            return JsonResponse({'success': True, 'message': 'Moved successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)

# ==========================================
# 5. Team Management (จัดการทีม)
# ==========================================
@login_required
def manage_team(request, team_id):
    # 1. ดึงข้อมูลทีม (เช็คด้วยว่าคนเรียกต้องเป็นสมาชิกทีมนี้เท่านั้น)
    team = get_object_or_404(Team, id=team_id, members=request.user)

    if request.method == 'POST':
        # รับ Username ที่ User กรอกมา
        username = request.POST.get('username')
        
        if username:
            try:
                # ค้นหา User ในระบบ
                user_to_add = User.objects.get(username=username)
                
                # เช็คว่าเขามีอยู่แล้วหรือยัง?
                if user_to_add in team.members.all():
                    messages.warning(request, f'User "{username}" is already in the team!')
                else:
                    team.members.add(user_to_add)
                    messages.success(request, f'Welcome! "{username}" has been added to the team.')
                    
            except User.DoesNotExist:
                messages.error(request, f'User "{username}" not found. Please check the spelling.')
        
        # รีโหลดหน้าเดิมเพื่อแสดงผลลัพธ์
        return redirect('tasks:manage_team', team_id=team_id)

    # ดึงรายชื่อสมาชิกทั้งหมดส่งไปหน้าเว็บ
    return render(request, 'tasks/manage_team.html', {
        'team': team,
        'members': team.members.all()
    })

@login_required
def remove_team_member(request, team_id, user_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    user_to_remove = get_object_or_404(User, id=user_id)
    
    # (Optional) ป้องกันการลบตัวเอง (เดี๋ยวไม่มีใครดูแลทีม)
    if user_to_remove == request.user:
        messages.error(request, "You cannot remove yourself from the team.")
    else:
        team.members.remove(user_to_remove)
        messages.success(request, f'{user_to_remove.username} was removed from the team.')
        
    return redirect('tasks:manage_team', team_id=team_id)