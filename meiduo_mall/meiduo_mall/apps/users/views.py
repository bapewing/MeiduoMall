import re

from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.serializers import CreateUserSerializer
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