from django import forms
from .models import Feedback
from .models import ContactSubmission

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your feedback...'}),
        }

class ContactSubmissionForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ['name', 'email']
