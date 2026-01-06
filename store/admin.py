from django.contrib import admin
from .models import Product # ดึงแบบแปลนสินค้ามา
from .models import Product, Order, OrderItem

admin.site.register(Product)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 # ไม่ต้องโชว์ช่องว่างๆ

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'total_price', 'created_at'] # โชว์คอลัมน์สำคัญ
    inlines = [OrderItemInline] # เอาตารางรายการของยัดเข้าไปในหน้า Order

admin.site.register(Order, OrderAdmin)