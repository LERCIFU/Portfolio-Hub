from django.db import migrations, models

class Task(models.Model):
    title = models.CharField(max_length=200) # ชื่อหัวข้อ
    completed = models.BooleanField(default=False) # ทำเสร็จหรือยัง?

    def __str__(self):
        return self.title