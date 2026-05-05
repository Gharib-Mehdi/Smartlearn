from django import forms


class QuizAnswerForm(forms.Form):
    choice_id = forms.IntegerField(widget=forms.HiddenInput())
