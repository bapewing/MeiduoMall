import re

from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.serializers import CreateUserSerializer, CheckSMSCodeSerializer, ResetPasswordSerializer, \
    UserDetailSerializer, EmailSerializer
from users.utils import get_user_by_account
from verifications.serializers import CheckImageCodeSerializer


class UserNameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        检查用户名是否存在
        :param request: 请求对象
        :param username: 用户名
        :return: 用户名/用户数量
        """
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机数量
    """

    def get(self, request, mobile):
        """
        检查手机号是否存在
        :param request: 请求对象
        :param mobile: 手机号
        :return: 手机号/手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class RegisterUserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """
    找回密码第一步验证
    """
    serializer_class = CheckImageCodeSerializer

    def get(self, request, account):
        """
        获取用户账号发送短信token
        :param request: 请求对象
        :param account: 用户名或手机号
        :return: 格式化手机号/access_token
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = get_user_by_account(account)
        if not user:
            return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        access_token = user.generate_send_sms_token()
        # TODO: 正则的sub方法
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

        return Response({
            'mobile': mobile,
            'access_token': access_token
        })


class PasswordTokenView(GenericAPIView):
    """
    找回密码第二步验证
    """
    serializer_class = CheckSMSCodeSerializer

    def get(self, request, account):
        """
        获取用户账号修改密码的token
        :param request: 请求对象
        :param account: 用户名或是密码
        :return: user_id/access_token
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})


# TODO： 不能继承UpdateAPIView吗？
class PasswordView(UpdateModelMixin, GenericAPIView):
    """
    重置用户密码
    """
    queryset = User.objects.all()
    serializer_class = ResetPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)


class UserDetailView(RetrieveAPIView):
    """
    用户详细信息
    """
    serializer_class = UserDetailSerializer
    # TODO: django认证系统
    permission_classes = [IsAuthenticated]

    # RetrieveAPIView只能自动处理url中包含pk的请求 /user/pk/
    # 现在的请求路由是 /user/ 所以需要重写get_object方法获取当前用户
    # 基于django的认证系统，request请求中存储有当前登录的用户
    # 前端请求时需要在headers中加入jwt token
    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    # queryset = User.objects.all()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    # def get_serializer(self, *args, **kwargs):
    #     return EmailSerializer(self.request.user, data=self.request.data)