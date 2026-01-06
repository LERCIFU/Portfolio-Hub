from django.shortcuts import render, redirect
from .models import Task

def index(request):
    # ถ้ามีการกดปุ่ม "บันทึก" (ส่งข้อมูลมา)
    if request.method == 'POST':
        title = request.POST.get('title') # หยิบชื่อที่เราพิมพ์
        Task.objects.create(title=title) # สั่งให้โกดังบันทึกของใหม่
        return redirect('/') # เพิ่มเสร็จแล้วให้โหลดหน้าเดิมใหม่

    # ถ้าแค่เปิดดูหน้าเว็บเฉยๆ
    tasks = Task.objects.all() # ไปหยิบของทั้งหมดมาโชว์
    return render(request, 'tasks/list.html', {'tasks': tasks})

def delete_task(request, pk):
    task = Task.objects.get(id=pk) # ไปหาของในโกดังที่รหัส (ID) ตรงกับที่เรากด
    task.delete() # สั่งทำลายทิ้งทันที!
    return redirect('/') # ลบเสร็จแล้วเด้งกลับหน้าแรก