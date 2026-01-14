from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from .models import (
    User,
    StudentProfile,
    Assignment,
    AssignmentInstance,
    Material,
    Question,
    Game,
    StudyPlan
)
from .forms import StudyPlanForm
import random
from datetime import date

# ---------------------------
# LANDING PAGE
# ---------------------------
def landing_page(request):
    return render(request, 'novae_app/landing.html')


# ---------------------------
# STUDENT LOGIN
# ---------------------------
class StudentLoginView(LoginView):
    template_name = 'novae_app/student_login.html'

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_student():
            return redirect('landing')  # Not a student account
        return super().form_valid(form)


# ---------------------------
# STUDENT DASHBOARD
# ---------------------------
from datetime import timedelta, date


from novae_app.models import User

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import AssignmentInstance, Material



@login_required
def student_dashboard(request):
    # ------------------------
    # Redirect non-student users
    # ------------------------
    if not hasattr(request.user, 'student_profile'):
        if hasattr(request.user, 'parent_profile'):
            return redirect('parent_dashboard')
        return redirect('landing')

    student = request.user.student_profile
    now = timezone.now()
    today = now.date()

    # ------------------------
    # Track total time spent on site (daily)
    # ------------------------
    session_start = request.session.get('session_start')

    if not session_start:
        request.session['session_start'] = now.timestamp()
        elapsed_seconds = 0
    else:
        elapsed_seconds = now.timestamp() - session_start

    if student.last_active_date != today:
        student.daily_time_seconds = 0
        student.last_active_date = today

    student.daily_time_seconds += int(elapsed_seconds)
    student.last_active_date = today
    student.save()

    request.session['session_start'] = now.timestamp()
    total_time_spent = timedelta(seconds=student.daily_time_seconds)

    # ------------------------
    # Fetch assignments and grades
    # ------------------------
    assignments = AssignmentInstance.objects.filter(
        student=student, completed=False
    ).order_by('assignment__due_date')

    grades = AssignmentInstance.objects.filter(
        student=student, completed=True, score__isnull=False
    )

    materials = Material.objects.filter(grade_level=student.grade)

    context = {
        'assignments': assignments,
        'grades': grades,
        'materials': materials,
        'total_time_spent': total_time_spent,
    }
    return render(request, 'novae_app/student_dashboard.html', context)

# ---------------------------
# STUDENT ASSIGNMENTS WITH PROGRESSIVE LOCKING
# ---------------------------
@login_required
def student_assignments(request):
    student = request.user.student_profile
    today = date.today()

    # Fetch all assignment instances for this student, ordered by due date
    all_instances = AssignmentInstance.objects.filter(student=student).order_by('assignment__due_date')

    accessible_assignments = []
    prev_score = 100  # Unlock first assignment by default

    for instance in all_instances:
        # Determine if the assignment is locked
        locked = False
        if prev_score < 75 and not instance.completed:
            locked = True

        # Build the assignment dictionary for the template
        accessible_assignments.append({
            'instance': instance,
            'locked': locked,
            'can_retake': instance.retake_allowed() if instance.completed else False,
            'completed': instance.completed,
            'score': instance.score
        })

        # Update prev_score if assignment is completed
        if instance.completed and instance.score is not None:
            prev_score = instance.score

    # Separate upcoming and past assignments
    upcoming_assignments = [
        item for item in accessible_assignments
        if item['instance'].assignment.due_date >= today
    ]

    past_assignments = [
        item for item in accessible_assignments
        if item['instance'].assignment.due_date < today
    ]

    # All grades (completed assignments with scores)
    grades = AssignmentInstance.objects.filter(student=student, completed=True, score__isnull=False)

    context = {
        'assignments': upcoming_assignments,
        'past_assignments': past_assignments,
        'grades': grades,
    }

    return render(request, 'novae_app/student_assignments.html', context)
# ---------------------------
# RETAKE ASSIGNMENT
# ---------------------------
@login_required
def student_assignment_retake(request, instance_id):
    instance = get_object_or_404(AssignmentInstance, id=instance_id, student=request.user.student_profile)

    if not instance.retake_allowed():
        return redirect('student_assignments')

    instance.start_retake()
    return redirect('student_assignment_detail', instance_id=instance.id)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import AssignmentInstance, StudentAnswer

@login_required
def student_assignment_detail(request, instance_id):
    student = request.user.student_profile
    instance = get_object_or_404(AssignmentInstance, id=instance_id, student=student)
    questions = instance.assignment.questions.all()

    if request.method == 'POST':
        # Save answers
        for question in questions:
            answer_text = request.POST.get(f'question_{question.id}', None)
            if question.question_type == 'TEXT' and answer_text:
                StudentAnswer.objects.create(
                    student=student,
                    question=question,
                    assignment_instance=instance,
                    text_answer=answer_text
                )
            elif question.question_type == 'MC' and answer_text:
                StudentAnswer.objects.create(
                    student=student,
                    question=question,
                    assignment_instance=instance,
                    selected_option=answer_text
                )

        # Mark assignment as completed
        instance.completed = True
        instance.save()

        return redirect('student_assignments')

    return render(request, 'novae_app/assignment_detail.html', {
        'instance': instance,
        'questions': questions
    })


# ---------------------------
# ASSIGNMENT DETAIL & AUTO-GRADE WITH LOCK
# ---------------------------
@login_required
def student_assignments(request):
    student = request.user.student_profile
    # Only show assignments that are NOT completed
    assignments = AssignmentInstance.objects.filter(student=student, completed=False).order_by('assignment__due_date')

    context = {
        'assignments': assignments
    }
    return render(request, 'novae_app/student_assignments.html', context)

# ---------------------------
# STUDENT GRADES
# ---------------------------
@login_required
def student_grades(request):
    student = request.user.student_profile
    grades = AssignmentInstance.objects.filter(student=student, score__isnull=False)
    return render(request, 'novae_app/student_grades.html', {'grades': grades})


# ---------------------------
# STUDENT MATERIALS
# ---------------------------
@login_required
def student_materials(request):
    student = request.user.student_profile
    materials = Material.objects.filter(grade_level=student.grade)
    return render(request, 'novae_app/student_materials.html', {'materials': materials})


# ---------------------------
# DAILY QUIZ
# ---------------------------
@login_required
def daily_quiz(request):
    questions = list(Question.objects.all())
    if not questions:
        return render(request, 'novae_app/daily_quiz.html', {'error': "No quiz questions available."})

    question = random.choice(questions)

    if request.method == 'POST':
        selected_option = request.POST.get('option')
        correct = (selected_option == question.correct_option)
        return render(request, 'novae_app/daily_quiz_result.html', {
            'question': question,
            'selected_option': selected_option,
            'correct': correct,
        })

    return render(request, 'novae_app/daily_quiz.html', {'question': question})


# ---------------------------
# LEARNING GAMES
# ---------------------------
@login_required
def learning_games_view(request):
    user_grade = request.user.student_profile.grade
    grade_number_map = {
        'K': 0, '1st': 1, '2nd': 2, '3rd': 3, '4th': 4,
        '5th': 5, '6th': 6, '7th': 7, '8th': 8, '9th': 9,
        '10th': 10, '11th': 11, '12th': 12
    }
    grade_number = grade_number_map.get(user_grade, 0)
    games = Game.objects.filter(min_grade__lte=grade_number, max_grade__gte=grade_number)
    return render(request, 'novae_app/learning_games.html', {'games': games})


# ---------------------------
# STUDY PLAN CRUD
# ---------------------------
@login_required
def study_plan_list(request):
    plans = StudyPlan.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'novae_app/study_plan_list.html', {'plans': plans})


@login_required
def study_plan_create(request):
    if request.method == 'POST':
        form = StudyPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.save()
            return redirect('study_plan_list')
    else:
        form = StudyPlanForm()
    return render(request, 'novae_app/study_plan_form.html', {'form': form})


@login_required
def study_plan_edit(request, pk):
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    if request.method == 'POST':
        form = StudyPlanForm(request.POST, instance=plan)
        if form.is_valid():
            sp = form.save(commit=False)
            sp.user = request.user
            sp.save()
            return redirect('study_plan_list')
    else:
        form = StudyPlanForm(instance=plan)
    return render(request, 'novae_app/study_plan_edit.html', {'form': form})


@login_required
def study_plan_delete(request, pk):
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    if request.method == 'POST':
        plan.delete()
        return redirect('study_plan_list')
    return render(request, 'novae_app/study_plan_confirm_delete.html', {'plan': plan})


# ---------------------------
# DOWNLOAD ASSIGNMENTS
# ---------------------------
@login_required
def download_assignment_docx(request, pk):
    assignment = get_object_or_404(Assignment, id=pk)
    doc = Document()
    doc.add_heading(assignment.title, level=1)
    doc.add_paragraph(f"Due Date: {assignment.due_date}")
    doc.add_paragraph("Description:")
    doc.add_paragraph(assignment.description or "No description provided.")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{assignment.title}.docx"'
    doc.save(response)
    return response


@login_required
def download_graded_assignment_docx(request, instance_id):
    instance = get_object_or_404(AssignmentInstance, id=instance_id)
    doc = Document()
    doc.add_heading(f"{instance.assignment.title} - Graded Review", level=1)
    doc.add_paragraph(f"Due Date: {instance.assignment.due_date}")
    doc.add_paragraph(f"Score: {instance.score or 'Not graded yet'}")
    doc.add_paragraph("Description:")
    doc.add_paragraph(instance.assignment.description or "No description provided.")
    doc.add_paragraph("Feedback:")
    doc.add_paragraph(instance.feedback or "No feedback provided.")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    filename = f"{instance.assignment.title}_graded_review.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    doc.save(response)
    return response


# ---------------------------
# PARENT LOGIN
# ---------------------------
class ParentLoginView(LoginView):
    template_name = 'novae_app/parent_login.html'

    def form_valid(self, form):
        user = form.get_user()
        if user.is_authenticated and user.is_parent():
            return super().form_valid(form)
        form.add_error(None, "You must log in as a parent.")
        return self.form_invalid(form)

    def get_success_url(self):
        return '/parent/dashboard/'


# ---------------------------
# PARENT DASHBOARD
# ---------------------------


from django.contrib.sessions.models import Session  # <-- ADD THIS
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime, timezone as py_timezone
from .models import AssignmentInstance

@login_required
def parent_dashboard(request):
    # Only allow parent users
    if not request.user.is_parent():
        return redirect('landing')

    children = request.user.parent_profile.children.all()
    children_data = []

    now = timezone.now()
    today = now.date()

    for child in children:
        # Graded assignments
        grades = AssignmentInstance.objects.filter(student=child, score__isnull=False)

        # Calculate total daily time spent
        total_seconds = 0

        # Only count time stored in StudentProfile for today
        student_profile = child
        if student_profile.last_active_date == today:
            total_seconds = student_profile.daily_time_seconds
        else:
            # Reset if not updated today
            student_profile.daily_time_seconds = 0
            student_profile.last_active_date = today
            student_profile.save()

        total_time_spent = timedelta(seconds=int(total_seconds))

        children_data.append({
            'student_id': child.id,   # ✅ ADD THIS
            'user': child.user,
            'grade': child.grade,
            'grades': grades,
            'total_time_spent': total_time_spent,
        })

    return render(request, 'novae_app/parent_dashboard.html', {'children': children_data})

# ---------------------------
# OTHER PAGES
# ---------------------------
@login_required
def achievements(request):
    return render(request, 'novae_app/achievements.html')


@login_required
def study_timer(request):
    return render(request, 'novae_app/study_timer.html')
from django.http import JsonResponse
from .models import AssignmentInstance, StudentProfile


from django.shortcuts import render
from django.http import JsonResponse
from .models import AssignmentInstance, StudentProfile

@login_required
def get_grades(request, child_id):
    # Fetch student profile by user ID
    try:
        student = StudentProfile.objects.get(user__id=child_id)
    except StudentProfile.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    # Fetch graded assignments for the student
    grades = AssignmentInstance.objects.filter(student=student, score__isnull=False)

    grades_data = []
    for grade in grades:
        grades_data.append({
            'assignment': grade.assignment.title,  # Assuming 'title' is a field in Assignment
            'score': grade.score,
            'comments': grade.feedback if grade.feedback else 'No feedback available',
        })

    return JsonResponse({'grades': grades_data})


def assignment_results(request, child_name):
    # Fetch the student
    student = get_object_or_404(User, username=child_name)

    # Fetch the AssignmentInstance for this student (only completed ones)
    assignments_instances = AssignmentInstance.objects.filter(student=student)

    # If no assignments found for this student
    if not assignments_instances:
        return render(request, 'novae_app/assignment_results.html', {'error': 'No assignments found'})

    # Prepare the data to pass to the template
    assignments_data = []

    for instance in assignments_instances:
        # Fetch questions related to the assignment
        questions = instance.assignment.questions.all()

        # Fetch the student's answers to the questions
        answers = Answer.objects.filter(assignment_instance=instance)  # Assuming Answer model exists

        # For each question, match the student's answer
        assignment_data = {
            'assignment': instance.assignment,
            'score': instance.score,
            'submitted_on': instance.submitted_on,
            'questions': []
        }

        for question in questions:
            # Find the student's answer (if exists)
            student_answer = answers.filter(question=question).first()

            assignment_data['questions'].append({
                'question_text': question.text,
                'correct_answer': question.correct_option,
                'student_answer': student_answer.answer_text if student_answer else 'Not answered',
                'is_correct': student_answer.is_correct if student_answer else False,
            })

        assignments_data.append(assignment_data)

    return render(request, 'novae_app/assignment_results.html', {'assignments_data': assignments_data})


@login_required
def parent_submitted_assignments(request, student_id):
    parent = request.user.parent_profile

    student = get_object_or_404(
        StudentProfile,
        id=student_id,
        parents=parent
    )

    assignments = AssignmentInstance.objects.filter(
        student=student,
        score__isnull=False  # only scored assignments
    ).select_related('assignment')

    print(f"Found {assignments.count()} graded assignments for student {student.id}")

    return render(
        request,
        'novae_app/student_grades.html',
        {
            'student': student,
            'grades': assignments
        }
    )

from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from django.forms import formset_factory
from novae_app.models import User, StudentProfile, ParentProfile
from django import forms

# ---------------------------
# Forms
# ---------------------------
class ParentSignUpForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class ChildForm(forms.Form):
    username = forms.CharField()
    grade = forms.ChoiceField(choices=[('K','K'), ('1st','1st'), ('2nd','2nd'), ('3rd', '3rd'),
    ('4th', '4th'),
    ('5th', '5th'),
    ('6th', '6th'),
    ('7th', '7th'),
    ('8th', '8th'),
    ('9th', '9th'),
    ('10th', '10th'),
    ('11th', '11th'),
    ('12th', '12th'), ])  # etc.
    password = forms.CharField(widget=forms.PasswordInput)

ChildFormSet = formset_factory(ChildForm, extra=1)

# ---------------------------
# View
# ---------------------------
def landing(request):
    return render(request, 'novae_app/landing.html')


from django.views.decorators.cache import never_cache

@never_cache
def student_signup(request):
    if request.method == 'POST':
        parent_form = ParentSignUpForm(request.POST)
        child_formset = ChildFormSet(request.POST)

        if parent_form.is_valid() and child_formset.is_valid():
            # Create parent and children
            parent_user = User.objects.create_user(
                username=parent_form.cleaned_data['username'],
                email=parent_form.cleaned_data['email'],
                password=parent_form.cleaned_data['password'],
                role='parent'
            )
            parent_profile = ParentProfile.objects.create(user=parent_user)

            for child_form in child_formset:
                username = child_form.cleaned_data.get('username')
                grade = child_form.cleaned_data.get('grade')
                password = child_form.cleaned_data.get('password')
                if username and grade and password:
                    child_user = User.objects.create_user(
                        username=username,
                        password=password,
                        role='student'
                    )
                    student_profile = StudentProfile.objects.create(
                        user=child_user,
                        grade=grade
                    )
                    parent_profile.children.add(student_profile)

            return redirect('landing')

    else:
        parent_form = ParentSignUpForm()
        child_formset = ChildFormSet()

    return render(request, 'student_signup.html', {
        'parent_form': parent_form,
        'child_formset': child_formset
    })

from django.shortcuts import render

def about_us(request):
    """
    About Us page for NovaeClass.
    Explains the platform, includes disclaimer and TOS.
    """
    return render(request, 'about_us.html')

from django.shortcuts import render, get_object_or_404, redirect
from .models import Assignment, Question, StudentProfile, StudentAnswer
from .forms import AssignmentSubmissionForm

def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = get_object_or_404(StudentProfile, user=request.user)

    # Get or create assignment instance
    instance, _ = AssignmentInstance.objects.get_or_create(
        assignment=assignment,
        student=student
    )

    questions = assignment.questions.all()

    if request.method == "POST":
        form = AssignmentSubmissionForm(questions, request.POST)

        if form.is_valid():
            correct_count = 0
            total_questions = questions.count()

            for question in questions:
                answer_value = form.cleaned_data.get(f'q_{question.id}')

                student_answer, _ = StudentAnswer.objects.update_or_create(
                    assignment_instance=instance,
                    question=question,
                    student=student
                )

                # ---------- TEXT QUESTION ----------
                if question.is_text_answer:
                    student_answer.text_answer = answer_value or ""

                    # Auto-grade text ONLY if correct_answer exists
                    if question.correct_answer:
                        if student_answer.text_answer.strip().lower() == question.correct_answer.strip().lower():
                            correct_count += 1

                # ---------- MULTIPLE CHOICE ----------
                else:
                    student_answer.selected_option = answer_value

                    if answer_value == question.correct_option:
                        correct_count += 1

                student_answer.save()

            # ---------- FINAL SCORE ----------
            instance.score = (correct_count / total_questions) * 100 if total_questions else 0
            instance.completed = True
            instance.save()

            return redirect('student_assignments')

    else:
        form = AssignmentSubmissionForm(questions)

    return render(request, 'submit_assignment.html', {
        'assignment': assignment,
        'form': form
    })
