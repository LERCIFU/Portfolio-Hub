from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order, OrderItem # รวม import ไว้บรรทัดเดียวกัน
from django.contrib.auth.decorators import login_required
import requests
from .forms import ProductForm
# 1. ฟังก์ชันเพิ่มของลงตะกร้า
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    # เก็บข้อมูลพื้นฐานลง Session (ใช้ id เป็น string)
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    
    request.session['cart'] = cart
    return redirect('cart_detail')

# 2. ฟังก์ชันดูของในตะกร้า
def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    for product_id, quantity in cart.items():
        # ป้องกัน error กรณีสินค้าถูกลบไปแล้วแต่ยังค้างในตะกร้า
        try:
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total_price += subtotal
            cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        except Product.DoesNotExist:
            continue
        
    return render(request, 'store/cart_detail.html', {
        'cart_items': cart_items, 
        'total_price': total_price
    })

# 3. ฟังก์ชันเคลียร์ตะกร้า
def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('product_list')

# 4. รายละเอียดสินค้า
def product_detail(request, pk):
    product = get_object_or_404(Product, id=pk) # ใช้ get_object_or_404 ปลอดภัยกว่า
    return render(request, 'store/product_detail.html', {'product': product})

# 5. หน้าร้านค้า (รวมระบบค้นหาไว้ในตัวเดียว)
def product_list(request):
    query = request.GET.get('search') # รับค่าจากช่องค้นหา
    if query:
        products = Product.objects.filter(name__icontains=query) # ค้นหาชื่อที่คล้ายกัน
    else:
        products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

# 6. สั่งซื้อและแจ้งเตือน Discord
def checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        # ตรวจสอบชื่อลูกค้าตามสถานะ Login
        if request.user.is_authenticated:
            customer_name = request.user.username  # ถ้า Login แล้วใช้ชื่อ User เลย
        else:
            customer_name = request.POST.get('customer_name') # ถ้ายังไม่ Login ใช้ชื่อที่กรอกมา

        if not cart:
            return redirect('product_list')

        # คำนวณยอดรวม
        total_price = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            total_price += product.price * quantity

        # สร้าง Order
        order = Order.objects.create(
            customer_name=customer_name,
            total_price=total_price
        )

        # สร้างข้อความ Discord
        discord_message = f"🔔 **ออเดอร์ใหม่มาแล้ว! (#{order.id})**\n"
        discord_message += f"👤 ลูกค้า: **{customer_name}**\n"
        discord_message += "---------------------------------\n"

        # บันทึกรายการสินค้า (OrderItem)
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
            discord_message += f"📦 {product.name} x {quantity} = {product.price * quantity} บ.\n"

        discord_message += "---------------------------------\n"
        discord_message += f"💰 **ยอดรวม: {total_price} บาท**"

        # ส่ง Webhook
        webhook_url = 'https://discord.com/api/webhooks/1458009167381139509/1gSu6Hhe-EQcwKE90Jd8Pko4yTm9S1kFjU2IDxB67arMUeBR2fTHUgyBjuMuwpQJcYsy'
        try:
            requests.post(webhook_url, json={'content': discord_message})
        except:
            print("ส่ง Discord ไม่ผ่าน แต่บันทึก DB แล้ว")

        # ล้างตะกร้า
        del request.session['cart']
        return render(request, 'store/success.html')
        
    return redirect('cart_detail')

@login_required # บังคับว่าต้อง Login ก่อนถึงจะเข้าหน้านี้ได้
def my_orders(request):
    # ค้นหา Order ที่ชื่อลูกค้า ตรงกับ ชื่อ User ที่ล็อกอินอยู่
    # .order_by('-created_at') คือเรียงจาก 'ล่าสุด' ไป 'เก่าสุด'
    orders = Order.objects.filter(customer_name=request.user.username).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

def add_product(request):
    # 🛡️ ระบบป้องกัน: ถ้าไม่ใช่ Admin ให้เด้งกลับไปหน้าร้านเลย
    if not request.user.is_superuser:
        return redirect('product_list')

    if request.method == 'POST':
        # รับข้อมูล + รับไฟล์รูปภาพ (request.FILES)
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() # บันทึกลง Database
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'store/add_product.html', {'form': form})

# ... (อย่าลืม import get_object_or_404 ด้านบนด้วยนะ ถ้ามีแล้วข้ามได้)

# 1. ฟังก์ชันแก้ไขสินค้า (Edit)
def edit_product(request, pk):
    if not request.user.is_superuser: # กันคนนอก
        return redirect('product_list')

    product = get_object_or_404(Product, id=pk) # ดึงสินค้าตัวที่จะแก้มา

    if request.method == 'POST':
        # instance=product คือหัวใจสำคัญ! บอกฟอร์มว่า "อัปเดตตัวนี้นะ ไม่ใช่สร้างใหม่"
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        # โหลดข้อมูลเดิมใส่ฟอร์มรอไว้
        form = ProductForm(instance=product)

    return render(request, 'store/edit_product.html', {'form': form, 'product': product})

# 2. ฟังก์ชันลบสินค้า (Delete)
def delete_product(request, pk):
    if not request.user.is_superuser:
        return redirect('product_list')

    product = get_object_or_404(Product, id=pk)

    if request.method == 'POST': # ถ้ากดปุ่ม "ยืนยันลบ"
        product.delete()
        return redirect('product_list')

    # ถ้าแค่กดเข้ามาดู จะพาไปหน้าถามย้ำ (Confirm Page)
    return render(request, 'store/delete_confirm.html', {'product': product})