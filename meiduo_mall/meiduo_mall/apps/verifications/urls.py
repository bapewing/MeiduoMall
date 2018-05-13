from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'image_codes/(?P<image_code_id>.+)/$', view=views.ImageCodeView.as_view(), name='image_codes'),
    url(r'sms_codes/(?P<mobile>1[35789]\d{9})/$', view=views.SMSCodeView.as_view(), name='sms_codes')
]
