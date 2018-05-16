from django.conf.urls import url

from oauth import views

urlpatterns = [
    url(r'qq/authorization/$', view=views.OauthQQUrlView.as_view()),

]