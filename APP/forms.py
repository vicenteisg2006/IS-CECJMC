from django import forms
from s3direct.widgets import S3DirectWidget

class MultimediaUploadForm(forms.Form):
    file = forms.URLField(
        widget=S3DirectWidget(dest='multimedia_upload'),
        label='Subir archivo'
    )
    post_id = forms.IntegerField(widget=forms.HiddenInput())