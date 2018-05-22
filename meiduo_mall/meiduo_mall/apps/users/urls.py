from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

from users import views

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', view=views.UserNameCountView.as_view(), name='usernames'),
    url(r'^mobiles/(?P<mobile>1[35789]\d{9})/count/$', view=views.MobileCountView.as_view(), name='mobiles'),
    # bug: user/$ 需要以$结尾，路由从上到下运行，路由的正则匹配不准确时，访问不到重置密码的路由
    url(r'^users/$', view=views.RegisterUserView.as_view(), name='users_login'),
    url(r'^authorizations/$', obtain_jwt_token, name='authorizations'),
    url(r'^accounts/(?P<account>\w{5,20})/sms/token/$', view=views.SMSCodeTokenView.as_view(), name='accounts_sms'),
    url(r'^accounts/(?P<account>\w{5,20})/password/token/$', view=views.PasswordTokenView.as_view(),
        name='accounts_pwd'),
    url(r'^users/(?P<pk>\d+)/password/$', view=views.PasswordView.as_view(), name='users_reset'),
    url(r'^user/$', view=views.UserDetailView.as_view(), name='user'),
    url(r'^emails/$', view=views.EmailView.as_view(), name='emails'),
    url(r'^emails/verification/$', view=views.EmailVerificationView.as_view(), name='email_verify'),
    url(r'browse_histories/$', views.UserHistoryView.as_view()),
]

router = DefaultRouter()
router.register('addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += router.urls
