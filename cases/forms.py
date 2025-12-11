"""
Forms for Case Management
"""
from django import forms
from cases.models import Case, CaseNote, CaseTimeline


class CaseForm(forms.ModelForm):
    """Form for creating/editing cases"""
    
    class Meta:
        model = Case
        fields = [
            'case_number', 'case_title', 'court_name', 'court_jurisdiction',
            'judge_name', 'status', 'filing_date', 'separation_date', 
            'marriage_date', 'expected_resolution_date',
            'estimated_marital_assets', 'estimated_separate_assets'
        ]
        widgets = {
            'case_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024-CV-001'
            }),
            'case_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Smith v. Smith'
            }),
            'court_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Superior Court of California'
            }),
            'court_jurisdiction': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Los Angeles County'
            }),
            'judge_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Hon. Jane Doe'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'filing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'separation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'marriage_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expected_resolution_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_marital_assets': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'estimated_separate_assets': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }
        labels = {
            'case_number': 'Case Number',
            'case_title': 'Case Title',
            'court_name': 'Court Name',
            'court_jurisdiction': 'Jurisdiction',
            'judge_name': 'Judge Name',
            'status': 'Case Status',
            'filing_date': 'Filing Date',
            'separation_date': 'Date of Separation',
            'marriage_date': 'Marriage Date',
            'expected_resolution_date': 'Expected Resolution Date',
            'estimated_marital_assets': 'Estimated Marital Assets ($)',
            'estimated_separate_assets': 'Estimated Separate Assets ($)',
        }
        help_texts = {
            'case_number': 'Court-assigned case number or internal reference',
            'separation_date': 'Critical date for determining marital vs. separate property',
            'estimated_marital_assets': 'Rough estimate of assets subject to division',
            'estimated_separate_assets': 'Rough estimate of non-marital assets',
        }


class CaseNoteForm(forms.ModelForm):
    """Form for creating case notes"""
    
    class Meta:
        model = CaseNote
        fields = ['title', 'content', 'category', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Note title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter your note here...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Note Title',
            'content': 'Note Content',
            'category': 'Category',
            'is_private': 'Private Note',
        }
        help_texts = {
            'is_private': 'Private notes are only visible to you',
        }


class CaseTimelineForm(forms.ModelForm):
    """Form for creating timeline events"""
    
    class Meta:
        model = CaseTimeline
        fields = [
            'event_date', 'event_title', 'event_description', 
            'event_type', 'is_key_event'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'event_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Filed petition for divorce'
            }),
            'event_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional details about this event...'
            }),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'is_key_event': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'event_date': 'Event Date',
            'event_title': 'Event Title',
            'event_description': 'Description',
            'event_type': 'Event Type',
            'is_key_event': 'Mark as Key Event',
        }
        help_texts = {
            'is_key_event': 'Key events appear in case summaries and reports',
        }