from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# ---------------------------
# User
# ---------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def is_student(self):
        return self.role == 'student'

    def is_parent(self):
        return self.role == 'parent'


# ---------------------------
# Grade Levels
# ---------------------------
GRADE_LEVEL_CHOICES = [
    ('K', 'Kindergarten'),
    ('1st', '1st Grade'),
    ('2nd', '2nd Grade'),
    ('3rd', '3rd Grade'),
    ('4th', '4th Grade'),
    ('5th', '5th Grade'),
    ('6th', '6th Grade'),
    ('7th', '7th Grade'),
    ('8th', '8th Grade'),
    ('9th', '9th Grade'),
    ('10th', '10th Grade'),
    ('11th', '11th Grade'),
    ('12th', '12th Grade'),
]


# ---------------------------
# Student Profile
# ---------------------------
from django.db import models
from django.utils import timezone
from datetime import date


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    grade = models.CharField(
        max_length=4,
        choices=GRADE_LEVEL_CHOICES,
        default='K',
        blank=True,
        null=True,
    )

    # New fields for daily site time tracking
    daily_time_seconds = models.PositiveIntegerField(default=0, help_text="Time spent on site today, in seconds")
    last_active_date = models.DateField(default=date.today, help_text="The date when daily_time_seconds was last updated")

    def __str__(self):
        return self.user.username


# ---------------------------
# Parent Profile
# ---------------------------
class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    children = models.ManyToManyField('StudentProfile', related_name='parents')

    def __str__(self):
        return self.user.username


# ---------------------------
# Assignment
# ---------------------------
class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    grade_level = models.CharField(
        max_length=10,
        choices=GRADE_LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text="If set, this assignment will be auto-assigned to all students in this grade."
    )

    def __str__(self):
        return f"{self.title} ({self.grade_level})"

# ---------------------------
# Assignment Instance (per student)
# ---------------------------
class AssignmentInstance(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='instances')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assignments')
    completed = models.BooleanField(default=False)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    attempts = models.PositiveIntegerField(default=0)  # ✅ track retake attempts

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.assignment.title} - {self.student.user.username}"

    # ---------------------------
    # Retake logic
    # ---------------------------
    def retake_allowed(self):
        """
        Return True if student can retake this assignment (score < 75).
        """
        return self.score is not None and self.score < 75

    def start_retake(self):
        """
        Prepare this instance for a retake.
        """
        self.completed = False
        self.score = None
        self.feedback = ""
        self.attempts += 1
        self.save()

    # ---------------------------
    # Auto-grade placeholder
    # ---------------------------
    def auto_grade(self, answers: dict):
        """
        Auto-grade assignment using a dictionary of answers {question_id: answer}.
        Returns the percentage score (0-100).
        """
        questions = self.assignment.questions.all()
        if not questions:
            return 0
        correct = 0
        for q in questions:
            if str(q.id) in answers and answers[str(q.id)] == q.correct_option:
                correct += 1
        score = (correct / questions.count()) * 100
        self.score = score
        self.completed = True
        self.save()
        return score


# ---------------------------
# Material
# ---------------------------
class Material(models.Model):
    title = models.CharField(max_length=200)
    file_url = models.URLField()
    grade_level = models.CharField(
        max_length=4,
        choices=GRADE_LEVEL_CHOICES,
        default='K',
    )

    def __str__(self):
        return f"{self.title} ({self.get_grade_level_display()})"


# ---------------------------
# Question
# ---------------------------
from django.db import models

class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('MC', 'Multiple Choice'),
        ('TEXT', 'Text Answer'),
    ]

    assignment = models.ForeignKey(
        'Assignment', 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=5,
        choices=QUESTION_TYPE_CHOICES,
        default='MC'
    )

    # MC fields (optional)
    option_a = models.CharField(max_length=255, blank=True, null=True)
    option_b = models.CharField(max_length=255, blank=True, null=True)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)
    correct_option = models.CharField(
        max_length=1,
        choices=[('A','A'),('B','B'),('C','C'),('D','D')],
        blank=True,
        null=True
    )

    @property
    def is_text_answer(self):
        return self.question_type == 'TEXT'

    def __str__(self):
        return f"{self.assignment.title}: {self.question_text[:50]}"

class StudentAnswer(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    assignment_instance = models.ForeignKey('AssignmentInstance', on_delete=models.CASCADE, related_name='answers')
    text_answer = models.TextField(blank=True, null=True)
    selected_option = models.CharField(max_length=255, blank=True, null=True)  # For MCQ
    submitted_at = models.DateTimeField(auto_now_add=True)

# ---------------------------
# Game
# ---------------------------
class Game(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField()
    min_grade = models.IntegerField()
    max_grade = models.IntegerField()

    def __str__(self):
        return self.title


# ---------------------------
# Study Plan
# ---------------------------
class StudyPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    class_name = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    date = models.DateField(null=True, blank=True)
    content = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


# ---------------------------
# SIGNAL: Auto-assign assignments to student on creation or grade update
# ---------------------------
@receiver(post_save, sender=StudentProfile)
def auto_assign_assignments(sender, instance, created, **kwargs):
    """
    When a student profile is created (or updated with a grade),
    assign all assignments for their grade automatically.
    """
    if instance.grade:
        assignments = Assignment.objects.filter(grade_level=instance.grade)
        for assignment in assignments:
            AssignmentInstance.objects.get_or_create(
                assignment=assignment,
                student=instance
            )

class StudySession(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)

    @property
    def duration_seconds(self):
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds()
        return 0

class StudentDailyTime(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    date = models.DateField()
    time_seconds = models.PositiveIntegerField(default=0)



