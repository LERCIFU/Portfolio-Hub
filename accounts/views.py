from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # บันทึกสมาชิกลง Database
            login(request, user) # สมัครเสร็จให้ Login อัตโนมัติเลย
            return redirect('product_list') # ส่งไปหน้าร้านค้า
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})