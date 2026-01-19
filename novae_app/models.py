from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date

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
# Billing / Access Control
# ---------------------------
class BillingProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_profile"
    )
    is_paid = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_id = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {'PAID' if self.is_paid else 'DEMO'}"


@receiver(post_save, sender=User)
def create_billing_profile(sender, instance, created, **kwargs):
    if created:
        BillingProfile.objects.create(user=instance)


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
# Course
# ---------------------------
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    grade_level = models.CharField(
        max_length=4,
        choices=GRADE_LEVEL_CHOICES
    )
    is_demo = models.BooleanField(
        default=False,
        help_text="Demo courses are accessible without payment."
    )

    def __str__(self):
        return f"{self.title} ({'Demo' if self.is_demo else 'Paid'})"


# ---------------------------
# Lesson
# ---------------------------
class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)
    is_sample = models.BooleanField(
        default=False,
        help_text="Sample lessons are accessible in demo mode."
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ---------------------------
# Student Profile
# ---------------------------
class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    grade = models.CharField(
        max_length=4,
        choices=GRADE_LEVEL_CHOICES,
        default='K',
        blank=True,
        null=True,
    )

    daily_time_seconds = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(default=date.today)
    is_demo = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


# ---------------------------
# Parent Profile
# ---------------------------
class ParentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile'
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    children = models.ManyToManyField(
        StudentProfile,
        related_name='parents'
    )

    def __str__(self):
        return self.user.username


# ---------------------------
# Assignment
# ---------------------------


class Assignment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="assignments",
        null=True,   # allow null in database
        blank=True   # allow blank in forms/admin
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    grade_level = models.CharField(
        max_length=10,
        choices=GRADE_LEVEL_CHOICES,
        blank=True,
        null=True
    )
    is_demo = models.BooleanField(default=False)
    is_sample = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# ---------------------------
# Assignment Instance
# ---------------------------
class AssignmentInstance(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='instances'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    completed = models.BooleanField(default=False)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    feedback = models.TextField(blank=True, null=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.assignment.title} - {self.student.user.username}"

    def retake_allowed(self):
        return self.score is not None and self.score < 75

    def start_retake(self):
        self.completed = False
        self.score = None
        self.feedback = ""
        self.attempts += 1
        self.save()


# ---------------------------
# Question
# ---------------------------
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('MC', 'Multiple Choice'),
        ('TEXT', 'Text Answer'),
    ]

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    is_text_answer = models.BooleanField(default=True)

    question_text = models.TextField()
    question_type = models.CharField(
        max_length=5,
        choices=QUESTION_TYPE_CHOICES,
        default='MC'
    )

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

    def __str__(self):
        return self.question_text[:50]
# --------------------------- # Game # --------------------------- 
class Game(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField()
    min_grade = models.IntegerField()
    max_grade = models.IntegerField()
    is_demo = models.BooleanField(default=False)  # ✅ add this if you need it

    def __str__(self):
        return self.title



# ---------------------------
# Student Answer
# ---------------------------
class StudentAnswer(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    assignment_instance = models.ForeignKey(
        AssignmentInstance,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    text_answer = models.TextField(blank=True, null=True)
    selected_option = models.CharField(max_length=1, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)





# ---------------------------
# Auto-assign Assignments
# ---------------------------
@receiver(post_save, sender=StudentProfile)
def auto_assign_assignments(sender, instance, **kwargs):
    if instance.grade:
        assignments = Assignment.objects.filter(
            grade_level=instance.grade
        )
        for assignment in assignments:
            AssignmentInstance.objects.get_or_create(
                assignment=assignment,
                student=instance
            )


# ---------------------------
# Time Tracking
# ---------------------------
class StudySession(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)

    @property
    def duration_seconds(self):
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds()
        return 0
class Material(models.Model):
    title = models.CharField(max_length=200)
    file_url = models.URLField()
    is_demo = models.BooleanField(default=False)
    is_sample = models.BooleanField(default=False)

    grade_level = models.CharField(
        max_length=4,
        choices=GRADE_LEVEL_CHOICES,
        default='K',
    )

    def __str__(self):
        return f"{self.title} ({self.get_grade_level_display()})"

class StudentDailyTime(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    date = models.DateField()
    time_seconds = models.PositiveIntegerField(default=0)

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

from django.db import models
from django.conf import settings

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


