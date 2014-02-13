from django import forms

from main.models import Cut_List, Episode


class EpisodeCommentForm(forms.ModelForm):
    """
    A form only to handle Episode comments
    """
    class Meta:
        model = Episode
        fields = ['id', 'comment']
        exclude = ['show']

        
class SimplifiedCutListForm(forms.ModelForm):
    apply = forms.ChoiceField(choices=((True, 'Use this video'), (False, 'Ignore')), 
                              widget=forms.RadioSelect())
    
    class Meta:
        model = Cut_List
        fields = ['id', 'apply']
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            if not kwargs.get('initial'):
                kwargs['initial'] = {}
            kwargs['initial']['apply'] = instance.apply and not instance.raw_file.trash
        return super(SimplifiedCutListForm, self).__init__(*args, **kwargs)

    