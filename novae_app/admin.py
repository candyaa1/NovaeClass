from django.contrib import admin
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
    list_display = ('user', 'grade')
    list_filter = ('grade',)
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
    """
    Form allows admin to assign an assignment to a grade.
    """
    grade_level = forms.ChoiceField(
        choices=[('', '--- Select Grade ---')] + list(Assignment._meta.get_field('grade_level').choices),
        required=False,
        help_text="Select grade to auto-assign this assignment to all students in that grade."
    )

    class Meta:
        model = Assignment
        fields = ['title', 'description','grade_level']


# ---------------------------
# Assignment admin
# ---------------------------
# ---------------------------
# Assignment admin
# ---------------------------
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # Show one empty form by default


@admin.register(Assignment)
class AssignmentAdmin(ImportExportModelAdmin):
    form = AssignmentAdminForm
    list_display = ('title', 'grade_level', 'due_date')
    list_filter = ('due_date', 'grade_level')
    search_fields = ('title',)
    inlines = [QuestionInline]  # Add questions inline

    def save_model(self, request, obj, form, change):
        """
        Save the assignment.
        Auto-assign to students is now handled by signals when students are created or updated.
        """
        super().save_model(request, obj, form, change)
        # ✅ No need to call obj.assign_to_grade_students() anymore

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
    list_display = ('title', 'grade_level', 'file_url')
    list_filter = ('grade_level',)
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
    list_display = ('title', 'min_grade', 'max_grade')
    list_filter = ('min_grade', 'max_grade')
    search_fields = ('title',)


# ---------------------------
# StudyPlan admin
# ---------------------------
@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'subject', 'date', 'updated_at')
    search_fields = ('title', 'user__username', 'subject')










