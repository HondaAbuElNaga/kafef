from django.contrib import admin
from .models import Exam, Question, StudentResponse

# نتيح إضافة الأسئلة داخل صفحة الامتحان مباشرة
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'created_at')

@admin.register(StudentResponse)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'submitted_at')
    # عشان تسمع الصوت من لوحة التحكم
    readonly_fields = ('audio_answer',)