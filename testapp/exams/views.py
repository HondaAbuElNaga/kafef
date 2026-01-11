from django.shortcuts import render, get_object_or_404, redirect
from .models import Exam, Question, StudentResponse ,Course, Lesson
from django.contrib.auth.models import User
from django.http import JsonResponse
import json


def home(request):
    """الصفحة الرئيسية للموقع"""
    return render(request, 'home.html')
# عرض قائمة الامتحانات
def exam_list(request):
    exams = Exam.objects.all()
    return render(request, 'exams/exam_list.html', {'exams': exams})

# عرض سؤال معين واستقبال الإجابة (شيلنا @login_required)
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        audio_file = request.FILES.get('audio_data')
        
        if question_id and audio_file:
            question = Question.objects.get(id=question_id)
            
            # حل سريع: لو المستخدم مش مسجل دخول، اعتبره هو الأدمن (أول مستخدم)
            if request.user.is_authenticated:
                student_user = request.user
            else:
                student_user = User.objects.first() # يجيب أول يوزر (الأدمن)

            StudentResponse.objects.create(
                student=student_user,
                question=question,
                audio_answer=audio_file
            )
            # هنا ممكن تخليه يفضل في نفس الصفحة عشان يجاوب باقي الأسئلة
            return redirect('take_exam', exam_id=exam.id)

    return render(request, 'exams/take_exam.html', {'exam': exam, 'questions': questions})



# ==========================================
# --- Views الخاصة بالدورات (الجديدة) ---
# ==========================================

def course_list(request):
    """عرض قائمة الدورات المتاحة"""
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    """عرض قائمة الدروس داخل دورة معينة"""
    course = get_object_or_404(Course, pk=course_id)
    lessons = course.lessons.all().order_by('order')
    return render(request, 'courses/lesson_list.html', {'course': course, 'lessons': lessons})

def lesson_player(request, lesson_id):
    """
    هذه هي أهم دالة.
    لا تقوم فقط بعرض الصفحة، بل تجهز سيناريو الدرس (JSON)
    لترسله لمحرك الجافاسكريبت.
    """
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    segments = lesson.segments.all().order_by('order')
    
    # تحويل البيانات إلى قائمة قواميس (JSON Structure)
    # هذا ما سيقرؤه الجافاسكريبت ليعرف ماذا يفعل خطوة بخطوة
    lesson_data = []
    for seg in segments:
        item = {
            'id': seg.id,
            'type': seg.segment_type,  # LECTURE, SIMULATOR, etc.
            'text': seg.text,
            'audio_url': seg.audio_file.url if seg.audio_file else '',
            
            # بيانات المحاكاة والخطأ (نرسلها فقط لو موجودة)
            'expected_key': seg.expected_key if seg.expected_key else '',
            'error_text': seg.error_text if seg.error_text else '',
            'error_audio_url': seg.error_audio_file.url if seg.error_audio_file else '',
        }
        lesson_data.append(item)

    context = {
        'lesson': lesson,
        # نحول القائمة لنص JSON آمن للاستخدام في القوالب
        'lesson_data_json': json.dumps(lesson_data, ensure_ascii=False) 
    }
    return render(request, 'courses/lesson_player.html', context)