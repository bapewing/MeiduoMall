from django.conf.urls import url

from users import views

urlpatterns = [
    url(r'users/', view=views.RegisterUserView.as_view(), name='users'),
    url(r'usernames/(?P<username>\w{5,20})/count/', view=views.UserNameCountView.as_view(), name='usernames'),
    url(r'mobiles/(?P<mobile>1[35789]\d{9})/count/', view=views.MobileCountView.as_view(), name='mobiles'),
]
