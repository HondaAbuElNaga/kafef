from django.db import models
from django.contrib.auth.models import User
import os
import asyncio
import edge_tts
from django.conf import settings
from django.core.files import File

# ==========================================
# 1. دوال المساعدة (Helpers)
# ==========================================

# الدالة الأساسية (Async)
async def generate_edge_audio(text, output_file):
    VOICE = "ar-SA-HamedNeural"
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

# دالة مساعدة جديدة (Sync Wrapper) لاستخدامها في الموديلات الجديدة بشكل أنظف
def generate_audio_sync(text, filename, storage_path):
    try:
        asyncio.run(generate_edge_audio(text, storage_path))
    except Exception:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_edge_audio(text, storage_path))
        loop.close()

# ==========================================
# 2. قسم الامتحانات (Exams System) - القديم
# ==========================================

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

        should_update = is_new or (original_title != self.title) or (original_desc != self.description)

        # أ) الصوت الكامل
        if should_update or not self.audio_file:
            try:
                text_full = (
                    f"أهلاً بك في {self.title}. "
                    f"{self.description}. "
                    "تعليمات هامة: "
                    "اضغط مسافه ضغطة واحدة لإعادة سماع السؤال. "
                    "اضغط مسافه ضغطتين بسرعة لبدء أو إيقاف التسجيل. "
                    "ملاحظة: يمكنك إعادة التسجيل أكثر من مرة، وسيتم اعتماد آخر محاولة. "
                    "اضغط إنتر لحفظ الإجابة والانتقال للسؤال التالي. "
                    "استخدم الأسهم للتنقل."
                    " حظاً موفقاً في امتحانك!"
                )
                self.generate_and_save_audio(text_full, f"exam_full_{self.id}.mp3", 'audio_file')
            except Exception as e:
                print(f"❌ خطأ في الصوت الكامل: {e}")

        # ب) الصوت المختصر
        if should_update or not self.short_audio:
            try:
                text_short = f"اختبار: {self.title}. {self.description}"
                self.generate_and_save_audio(text_short, f"exam_short_{self.id}.mp3", 'short_audio')
            except Exception as e:
                print(f"❌ خطأ في الصوت المختصر: {e}")

    def generate_and_save_audio(self, text, filename, field_name):
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
        os.makedirs(temp_path, exist_ok=True)
        full_path = os.path.join(temp_path, filename)
        generate_audio_sync(text, filename, full_path) # تم استخدام الدالة الموحدة هنا
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                getattr(self, field_name).save(filename, File(f), save=False)
            super(Exam, self).save(update_fields=[field_name])
            os.remove(full_path)
            print(f"✅ تم توليد ملف: {filename}")


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
            try: original_text = Question.objects.get(pk=self.pk).text
            except Question.DoesNotExist: pass

        super().save(*args, **kwargs)

        if is_new or (original_text != self.text) or not self.audio_file:
            try:
                filename = f"q_edge_{self.id}.mp3"
                temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
                os.makedirs(temp_path, exist_ok=True)
                full_path = os.path.join(temp_path, filename)

                generate_audio_sync(self.text, filename, full_path)
                
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


# ==========================================
# 3. قسم الدورات والدروس (Courses System) - الجديد
# ==========================================

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="اسم الدورة")
    description = models.TextField(verbose_name="وصف الدورة", blank=True)
    icon = models.ImageField(upload_to='courses_icons/', blank=True, null=True, verbose_name="صورة/أيقونة الدورة")
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.FileField(upload_to='courses_audio/', blank=True, null=True, verbose_name="صوت تعريف الدورة")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_title = None
        if not is_new:
            try: original_title = Course.objects.get(pk=self.pk).title
            except: pass

        super().save(*args, **kwargs)

        if is_new or (original_title != self.title) or not self.audio_file:
            try:
                text = f"دورة {self.title}. {self.description}"
                fname = f"course_{self.id}.mp3"
                temp = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
                os.makedirs(temp, exist_ok=True)
                fpath = os.path.join(temp, fname)
                
                generate_audio_sync(text, fname, fpath)
                
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        self.audio_file.save(fname, File(f), save=False)
                    super().save(update_fields=['audio_file'])
                    os.remove(fpath)
            except Exception as e:
                print(f"Error generating course audio: {e}")


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name="الدورة التابعة لها")
    title = models.CharField(max_length=200, verbose_name="عنوان الدرس")
    order = models.PositiveIntegerField(default=1, verbose_name="ترتيب الدرس")
    audio_file = models.FileField(upload_to='lessons_audio/', blank=True, null=True, verbose_name="صوت عنوان الدرس")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_title = None
        if not is_new:
            try: original_title = Lesson.objects.get(pk=self.pk).title
            except: pass
            
        super().save(*args, **kwargs)
        
        if is_new or (original_title != self.title) or not self.audio_file:
            try:
                text = f"درس: {self.title}"
                fname = f"lesson_{self.id}.mp3"
                temp = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
                os.makedirs(temp, exist_ok=True)
                fpath = os.path.join(temp, fname)
                
                generate_audio_sync(text, fname, fpath)
                
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        self.audio_file.save(fname, File(f), save=False)
                    super().save(update_fields=['audio_file'])
                    os.remove(fpath)
            except Exception as e:
                print(f"Error generating lesson audio: {e}")


class LessonSegment(models.Model):
    """
    وحدة الدرس (الفقرة).
    """
    TYPES = (
        ('LECTURE', 'شرح صوتي فقط'),
        ('SIMULATOR', 'محاكاة (انتظار ضغط زر)'),
        ('VOICE_Q', 'سؤال وتسجيل صوتي'),
        ('FILE_UPLOAD', 'رفع ملف (مستقبلي)'),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='segments')
    order = models.PositiveIntegerField(default=1, verbose_name="ترتيب الخطوة")
    segment_type = models.CharField(max_length=20, choices=TYPES, default='LECTURE', verbose_name="نوع الخطوة")
    
    # النص الأساسي
    text = models.TextField(verbose_name="نص الشرح/السؤال")
    
    # نص الخطأ (الجديد)
    error_text = models.TextField(
        blank=True, null=True, 
        verbose_name="رسالة الخطأ/التوضيح",
        help_text="هذا النص سيقرؤه النظام إذا أخطأ الطالب."
    )

    expected_key = models.CharField(
        max_length=50, blank=True, null=True, 
        help_text="مثال: Space, Enter, KeyC",
        verbose_name="زر الكيبورد المتوقع"
    )
    
    # الملفات الصوتية
    audio_file = models.FileField(upload_to='segments_audio/', blank=True, null=True, verbose_name="ملف الصوت الأساسي")
    error_audio_file = models.FileField(upload_to='segments_audio/errors/', blank=True, null=True, verbose_name="ملف صوت الخطأ")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.lesson.title} - Step {self.order}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_text = None
        original_error = None
        
        if not is_new:
            try: 
                obj = LessonSegment.objects.get(pk=self.pk)
                original_text = obj.text
                original_error = obj.error_text
            except: pass

        super().save(*args, **kwargs)

        # 1. الصوت الأساسي
        if is_new or (original_text != self.text) or not self.audio_file:
            try:
                fname = f"seg_{self.id}.mp3"
                temp = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
                os.makedirs(temp, exist_ok=True)
                fpath = os.path.join(temp, fname)
                
                generate_audio_sync(self.text, fname, fpath)
                
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        self.audio_file.save(fname, File(f), save=False)
                    super().save(update_fields=['audio_file'])
                    os.remove(fpath)
                    print(f"✅ Segment Audio Generated: {self.id}")
            except Exception as e:
                print(f"❌ Segment Error: {e}")

        # 2. صوت الخطأ
        if self.error_text and (is_new or (original_error != self.error_text) or not self.error_audio_file):
            try:
                fname = f"seg_err_{self.id}.mp3"
                temp = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
                os.makedirs(temp, exist_ok=True)
                fpath = os.path.join(temp, fname)
                
                generate_audio_sync(self.error_text, fname, fpath)
                
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        self.error_audio_file.save(fname, File(f), save=False)
                    super().save(update_fields=['error_audio_file'])
                    os.remove(fpath)
                    print(f"✅ Error Audio Generated: {self.id}")
            except Exception as e:
                print(f"❌ Error Audio Error: {e}")