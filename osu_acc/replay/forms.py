from django import forms


class ReplayForm(forms.Form):
    replay_file = forms.FileField(label='Select a file')
