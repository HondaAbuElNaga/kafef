from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Creates a superuser from environment variables if not exists'

    def handle(self, *args, **options):
        # تحميل ملف .env
        load_dotenv()

        # قراءة البيانات من الملف
        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.ERROR('❌ Error: Admin credentials not found in .env file'))
            return

        # التحقق: هل المستخدم موجود أصلاً؟
        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Creating superuser: {username}...'))
            
            # إنشاء المستخدم
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'ℹ️ Superuser "{username}" already exists.'))