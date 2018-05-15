from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token

from users import views

urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', view=views.UserNameCountView.as_view(), name='usernames'),
    url(r'mobiles/(?P<mobile>1[35789]\d{9})/count/', view=views.MobileCountView.as_view(), name='mobiles'),
    url(r'users/', view=views.RegisterUserView.as_view(), name='users'),
    url(r'^authorizations/$', obtain_jwt_token, name='authorizations'),
    url(r'accounts/(?P<account>\w{5,20})/sms/token/', view=views.SMSCodeTokenView.as_view(), name='accounts')
]
