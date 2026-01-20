from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models import Case, When, Value, IntegerField

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
    
    current_user_role = None 

    if current_team_id:
        current_team = get_object_or_404(Team, id=current_team_id, members=request.user)
        sprint_queryset = Sprint.objects.filter(team=current_team)
        
        membership = TeamMember.objects.filter(user=request.user, team=current_team).first()
        if membership:
            current_user_role = membership.role
    else:
        sprint_queryset = Sprint.objects.filter(created_by=request.user, team__isnull=True)
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
        
        tasks = active_sprint.tasks.select_related('assignee').annotate(
            priority_val=Case(
                When(priority='H', then=Value(3)),  
                When(priority='M', then=Value(2)),  
                When(priority='L', then=Value(1)),  
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-priority_val', '-created_at') 
        
      
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
        'current_user_role': current_user_role,
    }
    return render(request, 'tasks/list.html', context)


# ==========================================
# 2. Add Functions
# ==========================================
@login_required
def add_task(request):
    team_id = request.POST.get('team_id') or request.GET.get('team_id')
    
    # รับค่า URL หน้าเดิม (Next URL)
    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = TaskForm(request.POST, team_id=team_id)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user 
            
            if team_id:
                task.team = get_object_or_404(Team, id=team_id)
            else:
                task.team = None
            
            task.save()
            
            # ถ้ามี Next URL ให้กลับไปที่นั่นเลย
            if next_url:
                return redirect(next_url)
            
            # Fallback
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            else:
                return redirect('tasks:board')
    else:
        form = TaskForm(team_id=team_id)

    return render(request, 'tasks/task_form.html', {
        'form': form, 
        'title': 'Add New Task',
        'team_id': team_id,
        'next_url': next_url 
    })

@login_required
def add_sprint(request):
    team_id = request.POST.get('team_id') or request.GET.get('team_id')

    # เช็คสิทธิ์: MEMBER ห้ามสร้าง Sprint
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
                return redirect(f'/tasks/?team_id={team_id}&sprint={new_sprint.id}')
            else:
                return redirect(f'/tasks/?sprint={new_sprint.id}')
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
    
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, team_id=team_id)
        if form.is_valid():
            form.save()
            
            if next_url:
                return redirect(next_url)
            
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}')
            return redirect('tasks:board')
    else:
        form = TaskForm(instance=task, team_id=team_id)

    return render(request, 'tasks/task_form.html', {
        'form': form, 
        'title': '✏️ Edit Task', 
        'button_text': 'Save Changes',
        'next_url': next_url
    })

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    team_id = task.team.id if task.team else None
    
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
        current_user_role = 'MEMBER' # Default safe
        if task.team:
            mem = TeamMember.objects.filter(user=request.user, team=task.team).first()
            if mem: current_user_role = mem.role
        else:
            current_user_role = 'OWNER'

        # 🔥 Fix: ดึง URL หน้าปัจจุบันส่งไปให้ Partial View
        referer_url = request.META.get('HTTP_REFERER', '/tasks/')

        new_card_html = render_to_string('tasks/partials/task_card.html', {
            'task': task, 
            'current_user_role': current_user_role,
            'redirect_url': referer_url # 👈 ส่งตัวแปรนี้ไป!
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
            
            current_user_role = 'MEMBER'
            if task.team:
                mem = TeamMember.objects.filter(user=request.user, team=task.team).first()
                if mem: current_user_role = mem.role
            else:
                current_user_role = 'OWNER'

            # 🔥 Fix: ดึง URL หน้าปัจจุบันส่งไปให้ Partial View เช่นกัน
            referer_url = request.META.get('HTTP_REFERER', '/tasks/')

            new_card_html = render_to_string('tasks/partials/task_card.html', {
                'task': task,
                'current_user_role': current_user_role,
                'redirect_url': referer_url # 👈 ส่งตัวแปรนี้ไป!
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

@login_required
def start_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, pk=sprint_id)
    team_id = sprint.team.id if sprint.team else None

    if team_id:
        membership = TeamMember.objects.filter(user=request.user, team=sprint.team).first()
        if not membership or membership.role == 'MEMBER':
            messages.error(request, "❌ Access Denied.")
            return redirect(f'/tasks/?team_id={team_id}')

    active_sprint_query = Sprint.objects.filter(is_active=True)
    if team_id:
        active_sprint = active_sprint_query.filter(team=sprint.team).exists()
    else:
        active_sprint = active_sprint_query.filter(created_by=request.user, team__isnull=True).exists()

    if active_sprint:
        messages.error(request, "⚠️ มี Sprint อื่นกำลัง Active อยู่! กรุณากดจบงาน Sprint ปัจจุบันก่อน")
        if team_id: return redirect(f'/tasks/?team_id={team_id}')
        return redirect('tasks:board')

    sprint.is_active = True
    sprint.save()
    messages.success(request, f"🚀 Sprint '{sprint.name}' Started!")

    if team_id:
        return redirect(f'/tasks/?team_id={team_id}')
    return redirect('tasks:board')


@login_required
def complete_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, pk=sprint_id)
    team_id = sprint.team.id if sprint.team else None

    if team_id:
        membership = TeamMember.objects.filter(user=request.user, team=sprint.team).first()
        if not membership or membership.role == 'MEMBER':
            messages.error(request, "❌ Access Denied.")
            return redirect(f'/tasks/?team_id={team_id}')

    incomplete_tasks = sprint.tasks.exclude(status='DONE')
    count = incomplete_tasks.count()
    incomplete_tasks.update(sprint=None)

    sprint.is_active = False
    sprint.save()
    
    msg = f"🏁 Sprint Completed! "
    if count > 0:
        msg += f"({count} งานที่ยังไม่เสร็จ ถูกย้ายไป Backlog แล้ว)"
    messages.success(request, msg)

    if team_id:
        return redirect(f'/tasks/?team_id={team_id}')
    return redirect('tasks:board')

@login_required
def edit_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, pk=sprint_id)
    team_id = sprint.team.id if sprint.team else None

    if team_id:
        membership = TeamMember.objects.filter(user=request.user, team=sprint.team).first()
        if not membership or membership.role == 'MEMBER':
            messages.error(request, "❌ Access Denied: Admin/Owner only.")
            return redirect(f'/tasks/?team_id={team_id}')

    if request.method == 'POST':
        form = SprintForm(request.POST, instance=sprint)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sprint '{sprint.name}' updated!")
            if team_id:
                return redirect(f'/tasks/?team_id={team_id}&sprint={sprint.id}')
            return redirect(f'/tasks/?sprint={sprint.id}')
    else:
        form = SprintForm(instance=sprint)

    return render(request, 'tasks/sprint_form.html', {
        'form': form,
        'title': '✏️ Edit Sprint',
        'button_text': 'Save Changes',
        'team_id': team_id
    })

@login_required
def delete_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, pk=sprint_id)
    team_id = sprint.team.id if sprint.team else None

    if team_id:
        membership = TeamMember.objects.filter(user=request.user, team=sprint.team).first()
        if not membership or membership.role == 'MEMBER':
            messages.error(request, "❌ Access Denied: Admin/Owner only.")
            return redirect(f'/tasks/?team_id={team_id}')

    sprint.tasks.update(sprint=None)

    sprint.delete()
    messages.success(request, "Sprint deleted. Tasks moved to backlog.")

    if team_id:
        return redirect(f'/tasks/?team_id={team_id}')
    return redirect('tasks:board')

# tasks/views.py

@login_required
def dashboard(request):
    # 1. รับค่า team_id ก่อนเลย
    team_id = request.GET.get('team_id')
    current_team = None
    active_sprint = None

    if team_id:
        # 🏢 กรณีมี Team ID: ให้หาเฉพาะ Sprint ของทีมนั้น
        current_team = get_object_or_404(Team, id=team_id, members=request.user)
        active_sprint = Sprint.objects.filter(team=current_team, is_active=True).first()
    else:
        # 👤 กรณีไม่มี Team ID (Personal): ให้หาเฉพาะ Sprint ส่วนตัว (ที่ team เป็น NULL)
        active_sprint = Sprint.objects.filter(created_by=request.user, team__isnull=True, is_active=True).first()

    # 2. เตรียมตัวแปรเก็บสถิติ (เหมือนเดิม)
    stats = {
        'total_tasks': 0,
        'done_tasks': 0,
        'todo_tasks': 0,
        'progress_tasks': 0,
        'completion_rate': 0,
        'total_points': 0,
        'done_points': 0,
    }

    # 3. คำนวณ (เหมือนเดิมเป๊ะ)
    if active_sprint:
        tasks = active_sprint.tasks.all()
        stats['total_tasks'] = tasks.count()
        stats['done_tasks'] = tasks.filter(status='DONE').count()
        stats['todo_tasks'] = tasks.filter(status='TODO').count()
        stats['progress_tasks'] = tasks.filter(status='IN_PROGRESS').count()
        
        from django.db.models import Sum
        stats['total_points'] = tasks.aggregate(Sum('story_points'))['story_points__sum'] or 0
        stats['done_points'] = tasks.filter(status='DONE').aggregate(Sum('story_points'))['story_points__sum'] or 0

        if stats['total_tasks'] > 0:
            stats['completion_rate'] = int((stats['done_tasks'] / stats['total_tasks']) * 100)

    return render(request, 'tasks/dashboard.html', {
        'active_sprint': active_sprint,
        'stats': stats,
        'current_team': current_team,
    })