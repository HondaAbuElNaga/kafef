from django.db import models
from django.contrib.auth.models import User
import os
import asyncio
import edge_tts
from django.conf import settings
from django.core.files import File

# --- دالة توليد الصوت ---
async def generate_edge_audio(text, output_file):
    VOICE = "ar-SA-HamedNeural"
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

# --- جدول الامتحان ---
# --- جدول الامتحان ---
class Exam(models.Model):
    title = models.CharField(max_length=200, verbose_name="اسم الامتحان")
    description = models.TextField(verbose_name="وصف الامتحان", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 1. الملف الكامل (للترحيب داخل الامتحان)
    audio_file = models.FileField(upload_to='exams_audio/', blank=True, null=True, verbose_name="ملف الترحيب والتعليمات")
    
    # 2. الملف المختصر (للقائمة الخارجية)
    short_audio = models.FileField(upload_to='exams_audio/short/', blank=True, null=True, verbose_name="ملف القائمة المختصر")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # التحقق من التغييرات
        is_new = self.pk is None
        original_title = None
        original_desc = None
        
        if not is_new:
            try:
                original = Exam.objects.get(pk=self.pk)
                original_title = original.title
                original_desc = original.description
            except Exam.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # هل نحتاج لتحديث الأصوات؟
        should_update = is_new or (original_title != self.title) or (original_desc != self.description)

        # --- أ) توليد الصوت الكامل (بالتعليمات) ---
        if should_update or not self.audio_file:
            try:
                text_full = (
                    f"أهلاً بك في {self.title}. "
                    f"{self.description}. "
                    "تعليمات هامة: "
                    "اضغط  مسافه ضغطة واحدة لإعادة سماع السؤال. "
                    "اضغط مسافه ضغطتين بسرعة لبدء أو إيقاف التسجيل. "
                    "ملاحظة: يمكنك إعادة التسجيل أكثر من مرة، وسيتم اعتماد آخر محاولة. "
                    "اضغط إنتر لحفظ الإجابة والانتقال للسؤال التالي. "
                    "استخدم الأسهم للتنقل."
                    " حظاً موفقاً في امتحانك!"
                )
                self.generate_and_save_audio(text_full, f"exam_full_{self.id}.mp3", 'audio_file')
            except Exception as e:
                print(f"❌ خطأ في الصوت الكامل: {e}")

        # --- ب) توليد الصوت المختصر (للقائمة فقط) ---
        if should_update or not self.short_audio:
            try:
                text_short = f"اختبار: {self.title}. {self.description}"
                self.generate_and_save_audio(text_short, f"exam_short_{self.id}.mp3", 'short_audio')
            except Exception as e:
                print(f"❌ خطأ في الصوت المختصر: {e}")

    # دالة مساعدة لعدم تكرار الكود
    def generate_and_save_audio(self, text, filename, field_name):
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
        os.makedirs(temp_path, exist_ok=True)
        full_path = os.path.join(temp_path, filename)

        try:
            asyncio.run(generate_edge_audio(text, full_path))
        except Exception:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_edge_audio(text, full_path))
            loop.close()
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                getattr(self, field_name).save(filename, File(f), save=False)
            
            # تحديث الحقل فقط
            super(Exam, self).save(update_fields=[field_name])
            os.remove(full_path)
            print(f"✅ تم توليد ملف: {filename}")

# --- باقي الجداول (Question, StudentResponse) تبقى كما هي ---
class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="نص السؤال")
    order = models.PositiveIntegerField(default=1, verbose_name="ترتيب السؤال")
    audio_file = models.FileField(upload_to='questions_audio/', blank=True, null=True, verbose_name="ملف صوت السؤال")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_text = None
        if not is_new:
            try:
                original_text = Question.objects.get(pk=self.pk).text
            except Question.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # توليد صوت السؤال
        if is_new or (original_text != self.text) or not self.audio_file:
            try:
                filename = f"q_edge_{self.id}.mp3"
                temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
                os.makedirs(temp_path, exist_ok=True)
                full_path = os.path.join(temp_path, filename)

                try:
                    asyncio.run(generate_edge_audio(self.text, full_path))
                except Exception:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(generate_edge_audio(self.text, full_path))
                    loop.close()
                
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        self.audio_file.save(filename, File(f), save=False)
                    super().save(update_fields=['audio_file'])
                    os.remove(full_path)
                    print(f"✅ تم توليد صوت السؤال: {self.id}")
            except Exception as e:
                print(f"❌ خطأ: {e}")

class StudentResponse(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    audio_answer = models.FileField(upload_to='answers/%Y/%m/%d/', verbose_name="ملف الإجابة")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"إجابة الطالب {self.student.username} على {self.question.id}"