from django import forms
from .models import EvidenceDocument, EvidenceCollection

class EvidenceUploadForm(forms.ModelForm):
    class Meta:
        model = EvidenceDocument
        fields = ['document', 'title', 'document_type', 'document_date', 'description', 'is_privileged']
        widgets = {
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2023 Tax Return'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Context about this document...'}),
            'is_privileged': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EvidenceCollectionForm(forms.ModelForm):
    class Meta:
        model = EvidenceCollection
        fields = ['name', 'description', 'documents']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Collection Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documents': forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'height: 200px;'}),
        }