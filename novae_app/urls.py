from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import get_grades
from .views import student_signup
from django.shortcuts import redirect
from .views import landing
from .views import coming_soon

#replace coming_soon with return redirect('student_signup')  # Redirect to the signup page
#
# Simple redirect view for the homepage
def home_redirect(request):
    return redirect('student_signup')  # Redirect to the signup page
urlpatterns = [
    # ---------------------------
    # Landing & Logout
    # ---------------------------
    path('', home_redirect, name='home'),  # <-- root URL redirects to signup
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('landing/', landing, name='landing'),
    path('about/', views.about_us, name='about_us'),
    path("coming-soon/", coming_soon, name="coming_soon"),

    # ---------------------------
    # Student URLs
    # ---------------------------
    path('student/login/', views.StudentLoginView.as_view(), name='student_login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignments/<int:instance_id>/', views.student_assignment_detail, name='student_assignment_detail'),
    path('student/assignments/<int:instance_id>/retake/', views.student_assignment_retake, name='student_assignment_retake'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/materials/', views.student_materials, name='student_materials'),
    path('student/daily-quiz/', views.daily_quiz, name='daily_quiz'),
    path('student/learning-games/', views.learning_games_view, name='learning_games'),

    # Study Plan
    path('student/study-plans/', views.study_plan_list, name='study_plan_list'),
    path('student/study-plans/create/', views.study_plan_create, name='study_plan_create'),
    path('student/study-plans/<int:pk>/edit/', views.study_plan_edit, name='study_plan_edit'),
    path('student/study-plans/<int:pk>/delete/', views.study_plan_delete, name='study_plan_delete'),

# Assignment downloads
    path(
    'assignments/<int:pk>/download/',
    views.download_assignment_docx,
    name='assignment_download'
),
    path(
    'graded-assignments/<int:instance_id>/download/',
    views.download_graded_assignment_docx,
    name='graded_assignment_download'
),

# ---------------------------
# Parent URLs
    path(
    'parent/assignments/<int:student_id>/',
    views.parent_submitted_assignments,
    name='parent_submitted_assignments'
),
    path('student/signup/', student_signup, name='student_signup'),

    # ---------------------------
    path('parent/login/', views.ParentLoginView.as_view(), name='parent_login'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),

    # ---------------------------
    # Other Pages
    # ---------------------------
    path('achievements/', views.achievements, name='achievements'),
    path('study-timer/', views.study_timer, name='study_timer'),

    # Ensure these URLs are set correctly in your urls.py
    path('get-grades/<int:child_id>/', views.get_grades, name='get_grades'),
    path('assignment-results/<str:child_name>/', views.assignment_results, name='assignment_results'),
    path('billing/', views.billing_view, name='billing'),
    path(
        "assignment/preview/<int:assignment_id>/",
        views.assignment_preview,
        name="assignment_preview",
),
]
