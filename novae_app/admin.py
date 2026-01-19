from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from django import forms
from .models import (
    User,
    StudentProfile,
    ParentProfile,
    Assignment,
    AssignmentInstance,
    Material,
    Question,
    Game,
    Course,
    StudyPlan
)

# ---------------------------
# User admin
# ---------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')


# ---------------------------
# StudentProfile admin
# ---------------------------
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'grade', 'is_demo')
    list_filter = ('grade', 'is_demo')
    search_fields = ('user__username', 'user__email')



# ---------------------------
# ParentProfile admin
# ---------------------------
@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('children',)


# ---------------------------
# Assignment admin form
# ---------------------------
class AssignmentAdminForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Automatically assign "Free Trial" course for demo/sample
        if instance.is_demo or instance.is_sample:
            try:
                free_course = Course.objects.get(title="Free Trial")
                instance.course = free_course
            except Course.DoesNotExist:
                # fallback: pick any course if Free Trial doesn't exist
                instance.course = Course.objects.first()
        if commit:
            instance.save()
        return instance
# ---------------------------
# Assignment admin
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0



@admin.register(Assignment)
class AssignmentAdmin(ImportExportModelAdmin):
    form = AssignmentAdminForm
    list_display = (
        'title',
        'grade_level',
        'due_date',
        'is_demo',
        'is_sample',
    )
    list_filter = (
        'grade_level',
        'due_date',
        'is_demo',
        'is_sample',
    )
    search_fields = ('title',)
    inlines = [QuestionInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
# ---------------------------
# AssignmentInstance admin
# ---------------------------
@admin.register(AssignmentInstance)
class AssignmentInstanceAdmin(ImportExportModelAdmin):
    list_display = ('assignment', 'student', 'score', 'completed')
    list_filter = ('completed', 'assignment__grade_level')
    search_fields = ('assignment__title', 'student__user__username')


# ---------------------------
# Material admin
# ---------------------------
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'grade_level',
        'is_demo',
        'is_sample',
        'file_url',
    )
    list_filter = (
        'grade_level',
        'is_demo',
        'is_sample',
    )
    search_fields = ('title',)


# ---------------------------
# Question admin
# ---------------------------
from django.contrib import admin
from .models import Question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'question_type', 'is_text_answer', 'correct_option')
    list_filter = ('question_type',)
    search_fields = ('question_text',)


# ---------------------------
# Game admin
# ---------------------------
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'min_grade',
        'max_grade',
        'is_demo',
    )
    list_filter = (
        'min_grade',
        'max_grade',
        'is_demo',
    )
    search_fields = ('title',)



# ---------------------------
# StudyPlan admin
# ---------------------------
@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'subject', 'date', 'updated_at')
    search_fields = ('title', 'user__username', 'subject')










