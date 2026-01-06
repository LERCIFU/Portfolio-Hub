from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image'] # เลือกช่องที่จะให้กรอก
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อสินค้า'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'รายละเอียด'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ราคา'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }