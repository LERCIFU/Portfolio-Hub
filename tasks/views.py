from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from .models import Task, Sprint, Team, TeamMember
from .forms import TaskForm, SprintForm, TeamForm

# ==========================================
# 1. Main Board (หน้ากระดานงาน)
# ==========================================
@login_required
def task_board(request):
    my_teams = getattr(request.user, 'teams', None)
    if my_teams:
        my_teams = my_teams.all()
    else:
        my_teams = []

    current_team_id = request.GET.get('team_id')
    current_team = None
    sprint_queryset = Sprint.objects.none()
    
    # 🔥 ตัวแปรเก็บ Role ของคนปัจจุบัน (เอาไว้ส่งไปหน้า HTML)
    current_user_role = None 

    if current_team_id:
        current_team = get_object_or_404(Team, id=current_team_id, members=request.user)
        sprint_queryset = Sprint.objects.filter(team=current_team)
        
        # 🔥 เช็คว่า User เป็นตัวละครอะไรในทีมนี้ (Owner/Admin/Member)
        membership = TeamMember.objects.filter(user=request.user, team=current_team).first()
        if membership:
            current_user_role = membership.role
    else:
        sprint_queryset = Sprint.objects.filter(created_by=request.user, team__isnull=True)
        # ถ้าเป็น Personal ให้ถือว่าเป็น OWNER (ทำได้ทุกอย่าง)
        current_user_role = 'OWNER'

    all_sprints = sprint_queryset.order_by('-id')

    # --- Active Sprint ---
    sprint_id = request.GET.get('sprint')
    active_sprint = None

    if sprint_id:
        active_sprint = all_sprints.filter(pk=sprint_id).first()
    else:
        active_sprint = all_sprints.filter(is_active=True).first()

    # --- Tasks List ---
    tasks_todo = []
    tasks_in_progress = []
    tasks_done = []

    if active_sprint:
        tasks = active_sprint.tasks.select_related('assignee').all()
        tasks_todo = tasks.filter(status='TODO')
        tasks_in_progress = tasks.filter(status='IN_PROGRESS')
        tasks_done = tasks.filter(status='DONE')

    if current_team:
        backlog_tasks = Task.objects.filter(sprint__isnull=True, team=current_team).select_related('assignee')
    else:
        backlog_tasks = Task.objects.filter(sprint__isnull=True, team__isnull=True, created_by=request.user).select_related('assignee')

    context = {
        'my_teams': my_teams,
        'current_team': current_team,
        'active_sprint': active_sprint,
        'all_sprints': all_sprints,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_done': tasks_done,
        'backlog_tasks': backlog_tasks,
        'current_user_role': current_user_role, # 🔥 ส่ง Role ไปหน้าเว็บด้วย
    }
    return render(request, 'tasks/list.html', context)


# ==========================================
# 2. Add Functions
# ==========================================
@login_required
def add_task(request):
    team_id = request.POST.get('team_id') or request.GET.get('team_id')

    # (Note: ปกติ Member สร้างงานได้ ดังนั้นไม่ต้องกันสิทธิ์ตรงนี้)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, team_id=team_id)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user 
            
            if team_id:
                target_team = get_object_or_404(Team, id=team_id)
                task.team = target_team
            else:
                task.team = None

            active_sprint_query = Sprint.objects.filter(is_active=True)
            if team_id:
                active_sprint = active_sprint_query.filter(team_id=team_id).first()
            else:
                active_sprint = active_sprint_query.filter(created_by=request.user, team__isnull=True).first()

            if active_sprint:
                task.sprint = active_sprint
            
            task.save()
            
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            else:
                return redirect('tasks:board')
    else:
        form = TaskForm(team_id=team_id)

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Add New Task'})


@login_required
def add_sprint(request):
    team_id = request.POST.get('team_id') or request.GET.get('team_id')

    # 🔥 เช็คสิทธิ์: MEMBER ห้ามสร้าง Sprint
    if team_id:
        membership = TeamMember.objects.filter(user=request.user, team_id=team_id).first()
        if membership and membership.role == 'MEMBER':
            messages.error(request, "❌ สมาชิกทั่วไปไม่สามารถเริ่ม Sprint ได้ (ต้องเป็น Admin/Owner)")
            return redirect(f'/tasks/?team_id={team_id}')

    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            new_sprint = form.save(commit=False)
            new_sprint.created_by = request.user
            
            if team_id:
                target_team = get_object_or_404(Team, id=team_id)
                new_sprint.team = target_team
            else:
                new_sprint.team = None

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
                
                if old_sprint:
                    unfinished_tasks = old_sprint.tasks.exclude(status='DONE')
                    unfinished_tasks.update(sprint=new_sprint, source=old_sprint.name)
            else:
                new_sprint.save()
                
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            else:
                return redirect('tasks:board')
    else:
        form = SprintForm()

    return render(request, 'tasks/sprint_form.html', {
        'form': form, 
        'title': '🚀 Start New Sprint',
        'button_text': 'Start Sprint',
        'team_id': team_id
    })

@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            TeamMember.objects.create(user=request.user, team=team, role='OWNER')
            messages.success(request, f"Team '{team.name}' created successfully!")
            return redirect(f'/tasks/?team_id={team.id}')
    else:
        form = TeamForm()
    
    return render(request, 'tasks/create_team.html', {'form': form})


# ==========================================
# 3. Edit / Delete Functions
# ==========================================
@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    team_id = task.team.id if task.team else None
    
    # 🔥 1. รับค่า URL หน้าเดิมที่ส่งมา (ทั้งจาก GET หรือ POST)
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, team_id=team_id)
        if form.is_valid():
            form.save()
            
            # 🔥 2. ถ้ามีค่าหน้าเดิม ให้เด้งกลับไปที่นั่นเลย
            if next_url:
                return redirect(next_url)
            
            # Fallback (ถ้าไม่มี next ค่อยใช้ Logic เดิม)
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            return redirect('tasks:board')
    else:
        form = TaskForm(instance=task, team_id=team_id)

    return render(request, 'tasks/task_form.html', {
        'form': form, 
        'title': '✏️ Edit Task', 
        'button_text': 'Save Changes',
        'next_url': next_url # 🔥 3. ส่งต่อไปให้หน้า HTML ฝังไว้ในฟอร์ม
    })

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    team_id = task.team.id if task.team else None
    
    # 🔥 เช็คสิทธิ์: MEMBER ห้ามลบงาน (ถ้าเป็นงานทีม)
    if team_id:
        membership = TeamMember.objects.filter(user=request.user, team_id=team_id).first()
        if membership and membership.role == 'MEMBER':
            messages.error(request, "❌ คุณไม่มีสิทธิ์ลบงานนี้ (Member Role)")
            return redirect(f'/tasks/?team_id={team_id}')

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
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
        # 🔥 ต้องส่ง role ไปที่ card ด้วย ไม่งั้นปุ่มลบจะโผล่กลับมา
        current_user_role = 'MEMBER' # Default safe
        if task.team:
            mem = TeamMember.objects.filter(user=request.user, team=task.team).first()
            if mem: current_user_role = mem.role
        else:
            current_user_role = 'OWNER'

        new_card_html = render_to_string('tasks/partials/task_card.html', {
            'task': task, 
            'current_user_role': current_user_role # ส่ง Role ไปให้ Partial
        }, request=request)
        
        return JsonResponse({'success': True, 'html': new_card_html})

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
            
            # 🔥 ต้องส่ง role ไปที่ card ด้วยเช่นกัน
            current_user_role = 'MEMBER'
            if task.team:
                mem = TeamMember.objects.filter(user=request.user, team=task.team).first()
                if mem: current_user_role = mem.role
            else:
                current_user_role = 'OWNER'

            new_card_html = render_to_string('tasks/partials/task_card.html', {
                'task': task,
                'current_user_role': current_user_role
            }, request=request)

            return JsonResponse({
                'success': True, 
                'message': 'Moved successfully!',
                'html': new_card_html 
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)

# ==========================================
# 5. Team Management
# ==========================================
@login_required
def manage_team(request, team_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)

    # 🔥 เช็คสิทธิ์: MEMBER ห้ามเข้าหน้านี้
    membership = TeamMember.objects.filter(user=request.user, team=team).first()
    if not membership or membership.role == 'MEMBER':
        messages.error(request, "❌ Access Denied: Admin or Owner only.")
        return redirect(f'/tasks/?team_id={team_id}')

    if request.method == 'POST':
        username = request.POST.get('username')
        
        if username:
            try:
                user_to_add = User.objects.get(username=username)
                
                if TeamMember.objects.filter(user=user_to_add, team=team).exists():
                    messages.warning(request, f'User "{username}" is already in the team!')
                else:
                    TeamMember.objects.create(user=user_to_add, team=team, role='MEMBER')
                    messages.success(request, f'Welcome! "{username}" has been added to the team.')
                    
            except User.DoesNotExist:
                messages.error(request, f'User "{username}" not found.')
        
        return redirect('tasks:manage_team', team_id=team_id)

    memberships = TeamMember.objects.filter(team=team).select_related('user')
    
    return render(request, 'tasks/manage_team.html', {
        'team': team,
        'memberships': memberships
    })

@login_required
def remove_team_member(request, team_id, user_id):
    team = get_object_or_404(Team, id=team_id, members=request.user)
    
    # 🔥 เช็คสิทธิ์คนลบ (ต้องไม่ใช่ Member)
    current_membership = TeamMember.objects.filter(user=request.user, team=team).first()
    if not current_membership or current_membership.role == 'MEMBER':
        messages.error(request, "❌ Access Denied.")
        return redirect('tasks:manage_team', team_id=team_id)

    user_to_remove = get_object_or_404(User, id=user_id)
    if user_to_remove == request.user:
         pass 
         
    TeamMember.objects.filter(team=team, user=user_to_remove).delete()
    
    messages.success(request, f'{user_to_remove.username} was removed from the team.')
    return redirect('tasks:manage_team', team_id=team_id)