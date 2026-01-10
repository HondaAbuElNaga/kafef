from django.shortcuts import render, get_object_or_404, redirect
from .models import Exam, Question, StudentResponse
from django.contrib.auth.models import User

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