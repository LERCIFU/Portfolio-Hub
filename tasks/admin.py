from django.contrib import admin
from .models import Task # ดึง Model Task ที่เราสร้างไว้มาใช้งาน

admin.site.register(Task) # สั่งให้แสดงในหน้า Admin