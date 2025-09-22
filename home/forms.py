from django import forms
from .models import Feedback
from .models import ContactSubmission
from restaurant_management.utils import is_valid_email, normalize_email

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
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name'}),
        }

    def clean_email(self):
        """Validate email using our custom email validation utility"""
        email = self.cleaned_data.get('email')
        
        if email:
            # Normalize the email
            email = normalize_email(email)
            
            # Validate email format
            if not is_valid_email(email):
                raise forms.ValidationError("Please enter a valid email address.")
        
        return email
