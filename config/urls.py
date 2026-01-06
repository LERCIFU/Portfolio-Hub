"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # ต้องมีอันนี้
from django.conf.urls.static import static # ต้องมีอันนี้

admin.site.site_header = "Roblox Store Manager"       # ข้อความตรงแถบสีฟ้าด้านบน
admin.site.site_title = "Roblox Store Admin Portal"   # ชื่อตรง Tab ของ Browser
admin.site.index_title = "ยินดีต้อนรับสู่ระบบจัดการร้าน"  # ข้อความทักทายหน้าแรก

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
    path('store/', include('store.urls')),
    path('accounts/', include('accounts.urls')),
]

# ย้ายออกมาไว้นอก urlpatterns ตามที่ผมแนะนำไปคราวก่อน
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)