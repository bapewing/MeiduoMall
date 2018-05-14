from django.conf.urls import url

from users import views

urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', view=views.UserNameCountView.as_view(), name='usernames')
]
