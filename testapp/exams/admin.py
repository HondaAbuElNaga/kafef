from django.contrib import admin
from .models import Exam, Question, StudentResponse, Course, Lesson, LessonSegment

# ==========================================
# 1. تخصيص أدمن الامتحانات (النظام القديم)
# ==========================================

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # عدد الخانات الفاضية اللي تظهر زيادة

class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'has_audio')
    inlines = [QuestionInline] # ده عشان تضيف الأسئلة جوه صفحة الامتحان
    
    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = "يوجد ملف صوتي؟"

class StudentResponseAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'submitted_at')
    list_filter = ('student', 'submitted_at')

# ==========================================
# 2. تخصيص أدمن الدورات (النظام الجديد)
# ==========================================

# هذا الكلاس يسمح بإضافة فقرات الدرس (شرح/محاكاة) داخل صفحة الدرس نفسها
class LessonSegmentInline(admin.StackedInline): # Stacked عشان كل فقرة تاخد مساحة مريحة
    model = LessonSegment
    extra = 0
    fields = ('order', 'segment_type', 'text', 'expected_key', 'error_text', 'audio_file', 'error_audio_file')
    readonly_fields = ('audio_file', 'error_audio_file') # عشان ماترفعش ملف بالغلط، هو بيتولد أوتوماتيك

class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonSegmentInline] # السحر كله هنا

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')

# ==========================================
# 3. التسجيل في لوحة التحكم
# ==========================================
admin.site.register(Exam, ExamAdmin)
admin.site.register(Question) # ممكن نحتاجه لوحده أحياناً
admin.site.register(StudentResponse, StudentResponseAdmin)

admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
# مش محتاجين نسجل LessonSegment لوحده لأننا هانشوفه جوه Lesson