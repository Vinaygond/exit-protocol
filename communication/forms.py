from django import forms
from .models import Message
from cases.models import CaseParty

class BIFFGeneratorForm(forms.Form):
    """
    Form to input hostile text for AI rewriting.
    """
    received_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 4, 
            'placeholder': 'Paste the angry text/email you received here...'
        }),
        label="Hostile Message Received"
    )
    context = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 2, 
            'placeholder': 'Optional context (e.g. "Regarding pickup time")'
        }),
        label="Context"
    )

class MessageComposeForm(forms.ModelForm):
    """
    Form for composing secure messages.
    Dynamically filters recipients based on the active Case.
    """
    recipients = forms.ModelMultipleChoiceField(
        queryset=CaseParty.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="To:",
        help_text="Select one or more recipients."
    )
    
    apply_biff_filter = forms.BooleanField(
        required=False, 
        initial=False,
        label="Apply AI BIFF Filter (Beta)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Message
        fields = ['subject', 'original_body', 'priority']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'original_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Write your message here...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'original_body': 'Message Body'
        }

    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if case and user:
            # Only show parties associated with this specific case, excluding self
            self.fields['recipients'].queryset = CaseParty.objects.filter(
                case=case,
                is_active=True
            ).exclude(user=user).select_related('user')
            
            # Custom label to show Name + Role
            self.fields['recipients'].label_from_instance = lambda obj: f"{obj.user.get_full_name()} ({obj.get_role_display()})"