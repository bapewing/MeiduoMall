from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'image_codes/(?P<image_code_id>.+)/$', view=views.ImageCodeView.as_view(), name='image_codes')
]
