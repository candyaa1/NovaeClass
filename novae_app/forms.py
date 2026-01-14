from django import forms
from .models import StudyPlan


class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ['title', 'class_name', 'subject', 'date', 'notes', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'onenote-input-title',
                'placeholder': 'Study Plan Title',
            }),
            'class_name': forms.TextInput(attrs={
                'class': 'onenote-input-small',
                'placeholder': 'Class (e.g. Math 101)',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'onenote-input-small',
                'placeholder': 'Subject (e.g. Algebra)',
            }),
            'date': forms.DateInput(attrs={
                'class': 'onenote-input-small',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'onenote-input-notes',
                'placeholder': 'Additional Notes...',
                'rows': 3,
            }),
            'content': forms.Textarea(attrs={
                'class': 'onenote-input-content',
                'placeholder': 'Write your detailed study plan here...',
                'rows': 10,
            }),
        }

from django import forms
from django.forms import formset_factory
from novae_app.models import User, StudentProfile, ParentProfile

from django import forms
from django.forms import formset_factory

# Explicit list of grades for full dropdown
GRADES = [
    ('K', 'K'),
    ('1st', '1st'),
    ('2nd', '2nd'),
    ('3rd', '3rd'),
    ('4th', '4th'),
    ('5th', '5th'),
    ('6th', '6th'),
    ('7th', '7th'),
    ('8th', '8th'),
    ('9th', '9th'),
    ('10th', '10th'),
    ('11th', '11th'),
    ('12th', '12th'),
]

class ChildForm(forms.Form):
    username = forms.CharField(label="Child's Name")
    grade = forms.ChoiceField(
        choices=GRADES,
        label="Grade",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(widget=forms.PasswordInput)

# Formset for multiple children
ChildFormSet = formset_factory(ChildForm, extra=1)

from django import forms

class AssignmentSubmissionForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            if question.is_text_answer:
                # Text answer field
                self.fields[f'q_{question.id}'] = forms.CharField(
                    label=question.question_text,
                    widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your answer here...'}),
                    required=True
                )
            else:
                # Multiple choice
                choices = [
                    ('A', question.option_a),
                    ('B', question.option_b),
                    ('C', question.option_c),
                    ('D', question.option_d),
                ]
                self.fields[f'q_{question.id}'] = forms.ChoiceField(
                    label=question.question_text,
                    choices=choices,
                    widget=forms.RadioSelect,
                    required=True
                )
