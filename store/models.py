from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="ชื่อสินค้า")
    description = models.TextField(verbose_name="รายละเอียด")
    price = models.IntegerField(verbose_name="ราคา (บาท)")
    image = models.ImageField(upload_to='products/', verbose_name="รูปภาพสินค้า")
    script_file = models.FileField(upload_to='scripts/', blank=True, null=True, verbose_name="ไฟล์สคริปต์ (ถ้ามี)")
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    customer_name = models.CharField(max_length=200, verbose_name="ชื่อลูกค้า/Discord")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ยอดรวม")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="เวลาสั่งซื้อ")

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาต่อชิ้น")

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"