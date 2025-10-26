from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ResumeSubmission
import os

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=50, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if not email:
            raise forms.ValidationError('Email is required')
        if not password:
            raise forms.ValidationError('Password is required')
            
        return cleaned_data

class SignupForm(UserCreationForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    # Validate password match
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ResumeSubmissionForm(forms.ModelForm):
    class Meta:
        model = ResumeSubmission
        fields = ['resume_file', 'resume_text', 'target_role']

    def clean(self):
        cleaned = super().clean()
        resume_file = cleaned.get('resume_file')
        resume_text = cleaned.get('resume_text')
        target_role = cleaned.get('target_role')

        if not resume_file and not resume_text:
            raise forms.ValidationError('Please provide either a resume file or paste resume text.')

        # If file provided, validate extension
        if resume_file:
            name = resume_file.name.lower()
            valid_ext = ['.pdf', '.doc', '.docx']
            if not any(name.endswith(ext) for ext in valid_ext):
                raise forms.ValidationError('Unsupported file type. Use PDF, DOC or DOCX.')

        # target_role (job title) is optional here; job description can be supplied instead
        # if not target_role:
        #     raise forms.ValidationError('Please enter the target job role.')

        return cleaned

from django import forms

class ResumeUploadForm(forms.Form):
    resume_file = forms.FileField(
        label='Upload your Resume (.pdf, .docx, .txt)',
        required=True,
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf,.docx,.txt'})
    )
    job_description = forms.CharField(
        label='Job Description (Optional)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 50})
    )
